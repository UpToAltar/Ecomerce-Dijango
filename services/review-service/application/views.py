"""Review service API views."""
import logging
import threading
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.db.models import Avg, Count

from domain.models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer

logger = logging.getLogger(__name__)
PRODUCT_SERVICE_URL = getattr(settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000')


def _sync_product_rating(product_id):
    """After a review is created, re-calculate and push rating to product-service."""
    try:
        stats = Review.objects.filter(
            product_id=product_id, is_approved=True
        ).aggregate(avg=Avg('rating'), cnt=Count('id'))

        avg_rating = round(float(stats['avg'] or 0), 2)
        count = stats['cnt'] or 0

        requests.post(
            f'{PRODUCT_SERVICE_URL}/internal/products/{product_id}/update-rating/',
            json={'rating_avg': avg_rating, 'rating_count': count},
            timeout=5,
        )
    except Exception as e:
        logger.error(f'[ReviewService] sync rating failed for {product_id}: {e}')


class ReviewListView(APIView):
    """GET /api/reviews/ — List all reviews (with optional filters)."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Review.objects.filter(is_approved=True).order_by('-created_at')

        product_id = request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)

        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        rating = request.query_params.get('rating')
        if rating:
            qs = qs.filter(rating=int(rating))

        return Response(ReviewSerializer(qs[:100], many=True).data)


class ReviewCreateView(APIView):
    """POST /api/reviews/create/ — Submit a new review."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        # Prevent duplicate review (same user + product)
        if Review.objects.filter(user_id=d['user_id'], product_id=d['product_id']).exists():
            return Response(
                {'error': 'Bạn đã đánh giá sản phẩm này rồi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review = Review.objects.create(
            product_id=d['product_id'],
            user_id=d['user_id'],
            user_name=d.get('user_name', ''),
            rating=d['rating'],
            comment=d.get('comment', ''),
        )

        # Fire-and-forget: sync rating to product-service
        threading.Thread(
            target=_sync_product_rating,
            args=(str(d['product_id']),),
            daemon=True,
        ).start()

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDetailView(APIView):
    """GET /api/reviews/<id>/ — Single review detail.
       DELETE /api/reviews/<id>/ — Delete own review.
    """
    permission_classes = [AllowAny]

    def get(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
            return Response(ReviewSerializer(review).data)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=404)

    def delete(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=404)

        product_id = str(review.product_id)
        review.delete()

        # Re-sync rating after deletion
        threading.Thread(
            target=_sync_product_rating,
            args=(product_id,),
            daemon=True,
        ).start()

        return Response({'message': 'Review deleted'}, status=status.HTTP_200_OK)


class ProductReviewStatsView(APIView):
    """GET /api/reviews/product/<product_id>/stats/ — Rating breakdown for a product."""
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        qs = Review.objects.filter(product_id=product_id, is_approved=True)
        stats = qs.aggregate(avg=Avg('rating'), cnt=Count('id'))

        # Rating distribution
        distribution = {}
        for star in range(1, 6):
            distribution[star] = qs.filter(rating=star).count()

        return Response({
            'product_id': str(product_id),
            'rating_avg': round(float(stats['avg'] or 0), 2),
            'rating_count': stats['cnt'] or 0,
            'distribution': distribution,
        })
