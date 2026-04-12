import logging
from domain.models import Product

logger = logging.getLogger(__name__)


class ProductService:
    """Domain service for product business logic."""

    @staticmethod
    def decrease_stock(product_id, quantity):
        """Decrease stock for a product. Returns True on success."""
        try:
            product = Product.objects.select_for_update().get(id=product_id)
            if product.stock_quantity < quantity:
                return False
            product.stock_quantity -= quantity
            product.sold_count += quantity
            product.save(update_fields=['stock_quantity', 'sold_count', 'updated_at'])
            return True
        except Product.DoesNotExist:
            return False

    @staticmethod
    def increase_stock(product_id, quantity):
        """Restore stock (e.g. cancelled order)."""
        try:
            product = Product.objects.select_for_update().get(id=product_id)
            product.stock_quantity += quantity
            product.sold_count = max(0, product.sold_count - quantity)
            product.save(update_fields=['stock_quantity', 'sold_count', 'updated_at'])
            return True
        except Product.DoesNotExist:
            return False

    @staticmethod
    def update_rating(product_id, avg_rating, count):
        """Update product rating from review service."""
        try:
            product = Product.objects.get(id=product_id)
            product.rating_avg = avg_rating
            product.rating_count = count
            product.save(update_fields=['rating_avg', 'rating_count', 'updated_at'])
        except Product.DoesNotExist:
            pass
