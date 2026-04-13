"""Product views with Redis stock locking."""
import redis
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Count, F
from django.db import transaction
from django.conf import settings
from domain.models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
)


def _get_redis():
    return redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'redis'),
        port=int(getattr(settings, 'REDIS_PORT', 6379)),
        decode_responses=True,
    )


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for categories."""
    queryset = Category.objects.annotate(product_count=Count('products'))
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD for products with filtering, search, ordering."""
    queryset = Product.objects.select_related('category').filter(is_active=True)
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filterset_fields = ['category__slug', 'brand', 'is_active']
    search_fields = ['name', 'description', 'brand', 'sku']
    ordering_fields = ['price', 'created_at', 'sold_count', 'rating_avg', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        in_stock = self.request.query_params.get('in_stock')
        if in_stock == 'true':
            qs = qs.filter(stock_quantity__gt=0)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        return qs

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup = self.kwargs[lookup_url_kwarg]
        import uuid
        try:
            uuid.UUID(lookup)
            obj = queryset.get(id=lookup)
        except (ValueError, TypeError):
            obj = queryset.get(slug=lookup)
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """GET /api/products/featured/ — Top sold products."""
        products = self.get_queryset().order_by('-sold_count')[:12]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def check_stock(self, request, slug=None):
        """POST /api/products/{slug}/check_stock/ — Check stock availability."""
        product = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        return Response({
            'available': product.stock_quantity >= quantity,
            'stock_quantity': product.stock_quantity,
        })


class DeductStockView(APIView):
    """POST /internal/products/<product_id>/deduct-stock/
    Deduct stock with Redis distributed lock to prevent oversell.
    """
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        quantity = int(request.data.get('quantity', 1))
        lock_key = f'stock:lock:{product_id}'
        r = _get_redis()

        # Try to acquire lock (5 second TTL)
        acquired = r.set(lock_key, '1', nx=True, ex=5)
        if not acquired:
            return Response({'error': 'Stock operation in progress, retry'}, status=409)

        try:
            with transaction.atomic():
                try:
                    product = Product.objects.select_for_update().get(id=product_id)
                except Product.DoesNotExist:
                    return Response({'error': 'Product not found'}, status=404)

                if product.stock_quantity < quantity:
                    return Response({'error': 'Insufficient stock'}, status=400)

                product.stock_quantity = F('stock_quantity') - quantity
                product.sold_count = F('sold_count') + quantity
                product.save(update_fields=['stock_quantity', 'sold_count'])
                product.refresh_from_db()

            return Response({
                'success': True,
                'stock_quantity': product.stock_quantity,
            })
        finally:
            r.delete(lock_key)


class RestoreStockView(APIView):
    """POST /internal/products/<product_id>/restore-stock/
    Restore stock when order is cancelled/expired.
    """
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        quantity = int(request.data.get('quantity', 1))
        lock_key = f'stock:lock:{product_id}'
        r = _get_redis()

        acquired = r.set(lock_key, '1', nx=True, ex=5)
        if not acquired:
            return Response({'error': 'Stock operation in progress, retry'}, status=409)

        try:
            with transaction.atomic():
                try:
                    product = Product.objects.select_for_update().get(id=product_id)
                except Product.DoesNotExist:
                    return Response({'error': 'Product not found'}, status=404)

                product.stock_quantity = F('stock_quantity') + quantity
                product.sold_count = F('sold_count') - quantity
                product.save(update_fields=['stock_quantity', 'sold_count'])
                product.refresh_from_db()

            return Response({
                'success': True,
                'stock_quantity': product.stock_quantity,
            })
        finally:
            r.delete(lock_key)
