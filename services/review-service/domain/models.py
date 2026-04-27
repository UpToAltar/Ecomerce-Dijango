import uuid
from django.db import models


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    user_name = models.CharField(max_length=200, blank=True, default='')
    rating = models.IntegerField()
    comment = models.TextField(blank=True, default='')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = [('product_id', 'user_id')]

    def __str__(self):
        return f'Review {self.id} - {self.rating} stars'
