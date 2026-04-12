import uuid
from django.db import models
class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    user_id = models.UUIDField()
    rating = models.IntegerField()
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'reviews'
