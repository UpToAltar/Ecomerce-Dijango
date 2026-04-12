from rest_framework import viewsets, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, F
from domain.models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
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
        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        # In stock filter
        in_stock = self.request.query_params.get('in_stock')
        if in_stock == 'true':
            qs = qs.filter(stock_quantity__gt=0)
        # Category filter by slug
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        return qs

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
