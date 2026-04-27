import uuid
from django.db import models


class Shipment(models.Model):
    """A shipment tied to an order. One order has one shipment."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PICKED_UP = 'picked_up', 'Picked Up'
        IN_TRANSIT = 'in_transit', 'In Transit'
        OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'
        RETURNED = 'returned', 'Returned'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(unique=True, db_index=True)
    order_number = models.CharField(max_length=20, blank=True, default='')
    carrier = models.CharField(max_length=100, blank=True, default='Shop Delivery')
    tracking_number = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    shipping_address = models.JSONField(default=dict)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Shipment {self.tracking_number} - {self.status}'


class ShippingTracking(models.Model):
    """Timeline of tracking events for a shipment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=255, blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shipping_tracking'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.status} @ {self.location}'
