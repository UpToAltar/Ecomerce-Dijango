import uuid
from django.db import models
from domain.models import Product


class UserProductView(models.Model):
    """Tracks product views for AI recommendation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=100, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    source = models.CharField(max_length=50, blank=True, help_text='search, category, homepage, etc.')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_product_views'
        ordering = ['-created_at']


class UserSearchLog(models.Model):
    """Tracks user search queries for AI analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=100)
    query = models.CharField(max_length=255)
    results_count = models.IntegerField(default=0)
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_search_logs'
        ordering = ['-created_at']


class UserClickEvent(models.Model):
    """Tracks user interaction events for AI analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=100)
    event_type = models.CharField(
        max_length=50,
        help_text='product_click, add_to_cart, add_to_wishlist, share, etc.'
    )
    product_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'user_click_events'
        ordering = ['-created_at']
