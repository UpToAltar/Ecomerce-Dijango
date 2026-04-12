from rest_framework import serializers
from .models import UserProductView, UserSearchLog, UserClickEvent


class ProductViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProductView
        fields = ['product', 'session_id', 'user_id', 'source']

class SearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSearchLog
        fields = ['session_id', 'user_id', 'query', 'results_count', 'filters']

class ClickEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserClickEvent
        fields = ['session_id', 'user_id', 'event_type', 'product_id', 'metadata']
