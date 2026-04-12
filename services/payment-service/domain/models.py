import uuid
from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        COD = 'cod', 'Cash on Delivery'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOMO = 'momo', 'MoMo Wallet'
        VNPAY = 'vnpay', 'VNPay'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.COD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.id} - {self.method} - {self.status}'
