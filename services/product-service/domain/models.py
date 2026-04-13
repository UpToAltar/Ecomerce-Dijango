import uuid
from django.db import models


class Category(models.Model):
    """Product category — flat structure, no tree."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Single product model for all product types.
    Uses JSONB `specifications` for type-specific attributes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products'
    )
    brand = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    compare_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text='Original price before discount'
    )
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.IntegerField(default=0)
    sold_count = models.IntegerField(default=0)
    specifications = models.JSONField(
        default=dict, blank=True,
        help_text='Flexible attributes: {"ram": "8GB", "color": "Black"}'
    )
    image_url = models.URLField(max_length=500, blank=True)
    images = models.JSONField(
        default=list, blank=True,
        help_text='List of additional image URLs'
    )
    is_active = models.BooleanField(default=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def available_stock(self):
        from infrastructure.redis_client import RedisStockLock
        client = RedisStockLock()
        locked = client.get_locked_stock(str(self.id))
        return max(0, self.stock_quantity - locked)

    @property
    def is_in_stock(self):
        return self.available_stock > 0

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return int(
                (self.compare_price - self.price) / self.compare_price * 100
            )
        return 0
