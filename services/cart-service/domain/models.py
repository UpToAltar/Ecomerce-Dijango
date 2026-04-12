import uuid
from django.db import models


class CartItem(models.Model):
    """Shopping cart item — stores product_id and quantity only."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('user_id', 'product_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'Cart({self.user_id}) - Product({self.product_id}) x{self.quantity}'
