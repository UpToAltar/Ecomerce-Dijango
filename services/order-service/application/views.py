from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import requests
from domain.models import Order, OrderItem, ShippingTracking
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    ShippingTrackingSerializer,
)
from infrastructure.rabbitmq import publish_order_expiry, publish_event

PRODUCT_SERVICE_URL = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000')
PAYMENT_SERVICE_URL = getattr(settings, 'PAYMENT_SERVICE_URL', 'http://payment-service:8000')
SHIPPING_SERVICE_URL = getattr(settings, 'SHIPPING_SERVICE_URL', 'http://shipping-service:8000')


class OrderListView(APIView):
    """GET /api/orders/?user_id=... — List user's orders."""
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        qs = Order.objects.prefetch_related('items', 'tracking')
        if user_id:
            qs = qs.filter(user_id=user_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        orders_data = OrderSerializer(qs[:50], many=True).data

        # Fetch payment status for the batch
        order_ids = [str(data['id']) for data in orders_data]
        if order_ids:
            try:
                resp = requests.post(f'{PAYMENT_SERVICE_URL}/api/payments/batch/', json={'order_ids': order_ids}, timeout=5)
                if resp.status_code == 200:
                    payment_statuses = resp.json()
                    for data in orders_data:
                        data['payment_status'] = payment_statuses.get(str(data['id']), 'N/A')
                else:
                    for data in orders_data:
                        data['payment_status'] = 'N/A'
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'[OrderListView] Fetch payment statuses failed: {e}')
                for data in orders_data:
                    data['payment_status'] = 'N/A'

        return Response(orders_data)


class OrderCreateView(APIView):
    """POST /api/orders/create/ — Create new order."""
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        items_data = d['items']
        
        # 1. Deduct stock for all items FIRST
        # If any deduction fails, raise exception to rollback the transaction
        from rest_framework.exceptions import ValidationError
        deducted_items = []
        for item in items_data:
            try:
                resp = requests.post(
                    f'{PRODUCT_SERVICE_URL}/internal/products/{item["product_id"]}/lock-stock/',
                    json={'quantity': item['quantity']},
                    timeout=5,
                )
                if resp.status_code == 200:
                    deducted_items.append(item)
                else:
                    # Rollback potentially already deducted stock before raising
                    for d_item in deducted_items:
                        requests.post(
                            f'{PRODUCT_SERVICE_URL}/internal/products/{d_item["product_id"]}/release-stock/',
                            json={'quantity': d_item['quantity']},
                            timeout=5,
                        )
                    raise ValidationError({'error': f"Sản phẩm {item.get('product_name', item['product_id'])} không đủ tồn kho hoặc đang bị khoá."})
            except requests.RequestException as e:
                # Rollback potentially already deducted stock before raising
                for d_item in deducted_items:
                    try:
                        requests.post(
                            f'{PRODUCT_SERVICE_URL}/internal/products/{d_item["product_id"]}/release-stock/',
                            json={'quantity': d_item['quantity']},
                            timeout=5,
                        )
                    except:
                        pass
                import logging
                logging.getLogger(__name__).error(f'[OrderCreate] Deduct stock failed for {item["product_id"]}: {e}')
                raise ValidationError({'error': 'Không thể kết nối đến service sản phẩm để trừ tồn kho.'})

        total = sum(
            int(item['product_price']) * int(item['quantity'])
            for item in items_data
        )

        # Set expiry only for VNPay orders (5 minutes)
        payment_method = d.get('payment_method', 'cod')
        expires_at = None
        if payment_method == 'vnpay':
            expires_at = timezone.now() + timezone.timedelta(minutes=5)

        order = Order.objects.create(
            user_id=d['user_id'],
            total_amount=total + int(d.get('shipping_fee', 0)),
            shipping_fee=d.get('shipping_fee', 0),
            shipping_address=d['shipping_address'],
            payment_method=payment_method,
            note=d.get('note', ''),
            expires_at=expires_at,
        )

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                product_name=item.get('product_name', ''),
                product_price=item['product_price'],
                product_image=item.get('product_image', ''),
                quantity=item['quantity'],
                subtotal=int(item['product_price']) * int(item['quantity']),
            )

        # Publish DLX expiry message for VNPay orders
        if payment_method == 'vnpay':
            publish_order_expiry(str(order.id))

        # Publish order.created event
        publish_event(
            exchange='order.events',
            routing_key='order.created',
            payload={
                'order_id': str(order.id),
                'order_number': order.order_number,
                'user_id': str(order.user_id),
                'user_email': d.get('user_email', ''),
                'total_amount': str(order.total_amount),
                'payment_method': payment_method,
                'items': items_data,
            },
        )

        # Track purchase behavior (fire-and-forget)
        import threading
        def _track_purchases():
            for item in items_data:
                try:
                    requests.post(
                        f'{PRODUCT_SERVICE_URL}/api/analytics/event/',
                        json={
                            'user_id': str(d['user_id']),
                            'session_id': 'order-checkout',
                            'event_type': 'purchase',
                            'product_id': str(item['product_id']),
                            'metadata': {
                                'quantity': item['quantity'],
                                'price': str(item['product_price']),
                                'order_id': str(order.id),
                            },
                        },
                        timeout=3,
                    )
                except Exception:
                    pass
        threading.Thread(target=_track_purchases, daemon=True).start()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    """GET /api/orders/<id>/ — Order detail."""
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related('items', 'tracking').get(id=order_id)
            order_data = OrderSerializer(order).data
            
            # Fetch single payment status
            try:
                resp = requests.get(f'{PAYMENT_SERVICE_URL}/api/payments/order/{order_id}/', timeout=5)
                if resp.status_code == 200:
                    payments = resp.json()
                    if payments:
                        latest = sorted(payments, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                        order_data['payment_status'] = latest.get('status', 'N/A')
                    else:
                        order_data['payment_status'] = 'N/A'
                else:
                    order_data['payment_status'] = 'N/A'
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'[OrderDetail] Fetch payment status failed: {e}')
                order_data['payment_status'] = 'N/A'
                
            return Response(order_data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)


class OrderStatusUpdateView(APIView):
    """PUT /api/orders/<id>/status/ — Update order status (staff/admin)."""
    permission_classes = [AllowAny]

    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        order.status = new_status
        order.save()

        # Auto-create shipment when order moves to 'shipping'
        if new_status == 'shipping':
            import threading
            def _create_shipment():
                try:
                    requests.post(
                        f'{SHIPPING_SERVICE_URL}/api/shipping/create/',
                        json={
                            'order_id': str(order.id),
                            'order_number': order.order_number,
                            'shipping_address': order.shipping_address,
                        },
                        timeout=5,
                    )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f'[OrderStatusUpdate] create shipment failed: {e}')
            threading.Thread(target=_create_shipment, daemon=True).start()

        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    """PUT /api/orders/<id>/cancel/ — Cancel an order."""
    permission_classes = [AllowAny]

    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

        if order.status not in ('pending', 'confirmed'):
            return Response({'error': 'Cannot cancel this order'}, status=400)

        order.status = Order.Status.CANCELLED
        order.save()

        # Restore locked stock
        for item in order.items.all():
            try:
                requests.post(
                    f'{PRODUCT_SERVICE_URL}/internal/products/{item.product_id}/release-stock/',
                    json={'quantity': item.quantity},
                    timeout=5,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'[OrderCancelView] Stock restore failed for {item.product_id}: {e}')


        # Publish cancelled event
        publish_event(
            exchange='order.events',
            routing_key='order.cancelled',
            payload={
                'order_id': str(order.id),
                'order_number': order.order_number,
                'user_id': str(order.user_id),
            },
        )

        return Response(OrderSerializer(order).data)


class ShippingTrackingCreateView(APIView):
    """POST /api/orders/<id>/tracking/ — Add shipping tracking."""
    permission_classes = [AllowAny]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

        tracking = ShippingTracking.objects.create(
            order=order,
            status=request.data.get('status', ''),
            location=request.data.get('location', ''),
            note=request.data.get('note', ''),
        )
        return Response(ShippingTrackingSerializer(tracking).data, status=status.HTTP_201_CREATED)
