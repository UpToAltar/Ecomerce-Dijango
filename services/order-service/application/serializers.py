from rest_framework import serializers
from domain.models import Order, OrderItem, ShippingTracking


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'product_price', 'product_image', 'quantity', 'subtotal']


class ShippingTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingTracking
        fields = ['id', 'status', 'location', 'note', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking = ShippingTrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user_id', 'status', 'total_amount',
            'shipping_fee', 'shipping_address', 'payment_method', 'note',
            'items', 'tracking', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    shipping_address = serializers.JSONField()
    payment_method = serializers.CharField(default='cod')
    note = serializers.CharField(required=False, allow_blank=True, default='')
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=0, default=0)
    items = serializers.ListField(child=serializers.DictField())


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
