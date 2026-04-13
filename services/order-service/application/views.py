from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from domain.models import Order, OrderItem, ShippingTracking
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    ShippingTrackingSerializer,
)
from infrastructure.rabbitmq import publish_order_expiry, publish_event


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
        return Response(OrderSerializer(qs[:50], many=True).data)


class OrderCreateView(APIView):
    """POST /api/orders/create/ — Create new order."""
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        items_data = d['items']
        total = sum(
            int(item['product_price']) * int(item['quantity'])
            for item in items_data
        )

        # Set expiry only for VNPay orders (15 minutes)
        payment_method = d.get('payment_method', 'cod')
        expires_at = None
        if payment_method == 'vnpay':
            expires_at = timezone.now() + timezone.timedelta(minutes=15)

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
                'total_amount': str(order.total_amount),
                'payment_method': payment_method,
            },
        )

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
            return Response(OrderSerializer(order).data)
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
        order.status = serializer.validated_data['status']
        order.save()
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
