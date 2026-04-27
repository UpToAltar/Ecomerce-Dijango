from rest_framework import serializers
from domain.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Read serializer — returns full review data."""
    user_name = serializers.CharField(read_only=True, required=False, default='')

    class Meta:
        model = Review
        fields = [
            'id', 'product_id', 'user_id', 'user_name',
            'rating', 'comment', 'is_approved', 'created_at',
        ]
        read_only_fields = ['id', 'is_approved', 'created_at']


class ReviewCreateSerializer(serializers.Serializer):
    """Write serializer — validates input for creating a review."""
    product_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    user_name = serializers.CharField(max_length=200, required=False, default='')
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(allow_blank=True, default='')
