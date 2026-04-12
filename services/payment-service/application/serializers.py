from rest_framework import serializers
from domain.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    method = serializers.ChoiceField(choices=Payment.Method.choices, default='cod')
