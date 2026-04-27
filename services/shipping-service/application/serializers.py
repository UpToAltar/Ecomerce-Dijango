from rest_framework import serializers
from domain.models import Shipment, ShippingTracking


class ShippingTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingTracking
        fields = ['id', 'status', 'location', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    tracking_events = ShippingTrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'order_id', 'order_number', 'carrier', 'tracking_number',
            'status', 'shipping_address', 'estimated_delivery', 'actual_delivery',
            'tracking_events', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShipmentCreateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    order_number = serializers.CharField(max_length=20, required=False, default='')
    carrier = serializers.CharField(max_length=100, required=False, default='Shop Delivery')
    tracking_number = serializers.CharField(max_length=100, required=False, default='')
    shipping_address = serializers.JSONField(required=False, default=dict)
    estimated_delivery = serializers.DateTimeField(required=False, allow_null=True, default=None)


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.Status.choices)
    location = serializers.CharField(max_length=255, required=False, default='')
    note = serializers.CharField(required=False, default='')


class TrackingCreateSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=50)
    location = serializers.CharField(max_length=255, required=False, default='')
    note = serializers.CharField(required=False, default='')
