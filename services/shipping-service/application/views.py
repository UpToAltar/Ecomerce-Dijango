"""Shipping service API views."""
import logging
import random
import string
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone

from domain.models import Shipment, ShippingTracking
from .serializers import (
    ShipmentSerializer, ShipmentCreateSerializer,
    ShipmentStatusUpdateSerializer, TrackingCreateSerializer,
    ShippingTrackingSerializer,
)

logger = logging.getLogger(__name__)
ORDER_SERVICE_URL = getattr(settings, 'ORDER_SERVICE_URL', 'http://order-service:8000')


def _generate_tracking_number():
    """Generate a tracking number like 'SHP' + 10 random alphanumeric chars."""
    chars = string.ascii_uppercase + string.digits
    return 'SHP' + ''.join(random.choices(chars, k=10))


def _sync_order_status(order_id, new_status):
    """Sync shipment status back to order-service."""
    status_map = {
        'picked_up': 'shipping',
        'in_transit': 'shipping',
        'out_for_delivery': 'shipping',
        'delivered': 'delivered',
    }
    order_status = status_map.get(new_status)
    if order_status:
        try:
            requests.put(
                f'{ORDER_SERVICE_URL}/api/orders/{order_id}/status/',
                json={'status': order_status},
                timeout=5,
            )
        except Exception as e:
            logger.error(f'[ShippingService] sync order status failed: {e}')


class ShipmentListView(APIView):
    """GET /api/shipping/ — List shipments (filter by order_id, status)."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Shipment.objects.prefetch_related('tracking_events').all()

        order_id = request.query_params.get('order_id')
        if order_id:
            qs = qs.filter(order_id=order_id)

        order_status = request.query_params.get('status')
        if order_status:
            qs = qs.filter(status=order_status)

        return Response(ShipmentSerializer(qs[:50], many=True).data)


class ShipmentCreateView(APIView):
    """POST /api/shipping/create/ — Create a new shipment for an order."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ShipmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        # Prevent duplicate shipment for the same order
        if Shipment.objects.filter(order_id=d['order_id']).exists():
            return Response(
                {'error': 'Shipment already exists for this order.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tracking_number = d.get('tracking_number') or _generate_tracking_number()

        shipment = Shipment.objects.create(
            order_id=d['order_id'],
            order_number=d.get('order_number', ''),
            carrier=d.get('carrier', 'Shop Delivery'),
            tracking_number=tracking_number,
            shipping_address=d.get('shipping_address', {}),
            estimated_delivery=d.get('estimated_delivery'),
        )

        # Add initial tracking event
        ShippingTracking.objects.create(
            shipment=shipment,
            status='Tao don van chuyen',
            location='Kho hang',
            note=f'Don van chuyen {tracking_number} da duoc tao.',
        )

        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class ShipmentDetailView(APIView):
    """GET /api/shipping/<id>/ — Shipment detail with tracking events."""
    permission_classes = [AllowAny]

    def get(self, request, shipment_id):
        try:
            shipment = Shipment.objects.prefetch_related('tracking_events').get(id=shipment_id)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)


class ShipmentByOrderView(APIView):
    """GET /api/shipping/order/<order_id>/ — Get shipment by order_id."""
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        try:
            shipment = Shipment.objects.prefetch_related('tracking_events').get(order_id=order_id)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'No shipment for this order'}, status=404)


class ShipmentStatusUpdateView(APIView):
    """PUT /api/shipping/<id>/status/ — Update shipment status (auto-adds tracking event)."""
    permission_classes = [AllowAny]

    def put(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)

        serializer = ShipmentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        old_status = shipment.status
        shipment.status = d['status']

        if d['status'] == Shipment.Status.DELIVERED:
            shipment.actual_delivery = timezone.now()

        shipment.save()

        # Auto-create tracking event
        status_labels = {
            'pending': 'Cho xu ly',
            'picked_up': 'Da lay hang',
            'in_transit': 'Dang van chuyen',
            'out_for_delivery': 'Dang giao hang',
            'delivered': 'Da giao thanh cong',
            'failed': 'Giao hang that bai',
            'returned': 'Da hoan tra',
        }
        ShippingTracking.objects.create(
            shipment=shipment,
            status=status_labels.get(d['status'], d['status']),
            location=d.get('location', ''),
            note=d.get('note', ''),
        )

        # Sync status back to order-service
        _sync_order_status(str(shipment.order_id), d['status'])

        return Response(ShipmentSerializer(
            Shipment.objects.prefetch_related('tracking_events').get(id=shipment_id)
        ).data)


class ShipmentTrackingCreateView(APIView):
    """POST /api/shipping/<id>/tracking/ — Add a tracking event manually."""
    permission_classes = [AllowAny]

    def post(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)

        serializer = TrackingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        tracking = ShippingTracking.objects.create(
            shipment=shipment,
            status=d['status'],
            location=d.get('location', ''),
            note=d.get('note', ''),
        )
        return Response(ShippingTrackingSerializer(tracking).data, status=status.HTTP_201_CREATED)


class TrackByTrackingNumberView(APIView):
    """GET /api/shipping/track/<tracking_number>/ — Public tracking lookup."""
    permission_classes = [AllowAny]

    def get(self, request, tracking_number):
        try:
            shipment = Shipment.objects.prefetch_related('tracking_events').get(
                tracking_number=tracking_number
            )
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Tracking number not found'}, status=404)


class ShipmentAdminListView(APIView):
    """GET /api/shipping/admin/ — List ALL shipments with filters (admin/staff)."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Shipment.objects.prefetch_related('tracking_events').all()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(tracking_number__icontains=search) | qs.filter(order_number__icontains=search)
        limit = min(int(request.query_params.get('limit', 100)), 200)
        return Response(ShipmentSerializer(qs[:limit], many=True).data)
