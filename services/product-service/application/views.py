"""Product views with Redis stock locking."""
import logging
import threading
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

logger = logging.getLogger(__name__)


def _extract_user_id(request):
    uid = (
        request.META.get('HTTP_X_USER_ID')
        or request.query_params.get('user_id')
        or request.data.get('user_id')
    )
    return str(uid) if uid else None


def _extract_session_id(request):
    return (
        request.META.get('HTTP_X_SESSION_ID')
        or request.query_params.get('session_id')
        or 'anonymous'
    )


def _track_product_view(product_id, user_id, session_id, source='product_detail'):
    try:
        from analytics.models import UserProductView
        import uuid
        UserProductView.objects.create(
            product_id=product_id,
            user_id=uuid.UUID(str(user_id)) if user_id else None,
            session_id=session_id or 'anonymous',
            source=source,
        )
    except Exception as e:
        logger.debug(f"[analytics] view track failed: {e}")


def _track_search(user_id, session_id, query, results_count, filters=None):
    try:
        from analytics.models import UserSearchLog
        import uuid
        UserSearchLog.objects.create(
            user_id=uuid.UUID(str(user_id)) if user_id else None,
            session_id=session_id or 'anonymous',
            query=query[:255],
            results_count=results_count,
            filters=filters or {},
        )
    except Exception as e:
        logger.debug(f"[analytics] search track failed: {e}")


def _track_click_event(user_id, session_id, event_type, product_id, metadata=None):
    try:
        from analytics.models import UserClickEvent
        import uuid
        UserClickEvent.objects.create(
            user_id=uuid.UUID(str(user_id)) if user_id else None,
            session_id=session_id or 'anonymous',
            event_type=event_type,
            product_id=uuid.UUID(str(product_id)) if product_id else None,
            metadata=metadata or {},
        )
    except Exception as e:
        logger.debug(f"[analytics] click track failed: {e}")


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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        user_id = _extract_user_id(request)
        session_id = _extract_session_id(request)
        threading.Thread(
            target=_track_product_view,
            args=(instance.id, user_id, session_id, 'product_detail'),
            daemon=True,
        ).start()
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        search_query = request.query_params.get('search', '').strip()
        if search_query:
            user_id = _extract_user_id(request)
            session_id = _extract_session_id(request)
            data = response.data
            results_count = len(data.get('results', data)) if isinstance(data, dict) else len(data)
            filters = {
                k: v for k, v in request.query_params.items()
                if k not in ('search', 'page', 'limit', 'user_id', 'session_id')
            }
            threading.Thread(
                target=_track_search,
                args=(user_id, session_id, search_query, results_count, filters),
                daemon=True,
            ).start()
        return response

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


class LockStockView(APIView):
    """POST /internal/products/<product_id>/lock-stock/
    Increments Redis lock without changing DB.
    """
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        from infrastructure.redis_client import RedisStockLock
        client = RedisStockLock()
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            if product.available_stock < quantity:
                return Response({'error': 'Insufficient available stock'}, status=400)
            
            client.lock_stock(str(product_id), quantity)
            return Response({'success': True, 'available_stock': product.available_stock})
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class CommitStockView(APIView):
    """POST /internal/products/<product_id>/commit-stock/
    Decrements DB stock and removes Redis lock.
    """
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        from infrastructure.redis_client import RedisStockLock
        client = RedisStockLock()
        quantity = int(request.data.get('quantity', 1))
        
        lock_key = f'stock:lock:commit:{product_id}'
        r = _get_redis()
        # use distributed lock to prevent race condition during DB update
        acquired = r.set(lock_key, '1', nx=True, ex=5)
        if not acquired:
            return Response({'error': 'Stock operation in progress, retry'}, status=409)

        try:
            with transaction.atomic():
                try:
                    product = Product.objects.select_for_update().get(id=product_id)
                except Product.DoesNotExist:
                    return Response({'error': 'Product not found'}, status=404)

                product.stock_quantity = F('stock_quantity') - quantity
                product.sold_count = F('sold_count') + quantity
                product.save(update_fields=['stock_quantity', 'sold_count'])
                
            client.release_lock(str(product_id), quantity)
            product.refresh_from_db()
            return Response({
                'success': True,
                'available_stock': product.available_stock,
            })
        finally:
            r.delete(lock_key)


class ReleaseStockDelockView(APIView):
    """POST /internal/products/<product_id>/release-stock/
    Releases Redis lock without changing DB.
    """
    permission_classes = [AllowAny]

    def post(self, request, product_id):
        from infrastructure.redis_client import RedisStockLock
        client = RedisStockLock()
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
            client.release_lock(str(product_id), quantity)
            return Response({'success': True, 'available_stock': product.available_stock})
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
