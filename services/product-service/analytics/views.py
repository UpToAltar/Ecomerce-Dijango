from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserProductView, UserSearchLog, UserClickEvent
from .serializers import ProductViewSerializer, SearchLogSerializer, ClickEventSerializer


class TrackProductView(generics.CreateAPIView):
    serializer_class = ProductViewSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)


class TrackSearchView(generics.CreateAPIView):
    serializer_class = SearchLogSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)


class TrackClickEventView(generics.CreateAPIView):
    serializer_class = ClickEventSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)


class BehaviorDataView(APIView):
    """Internal endpoint: returns raw behavior data for AI service training."""
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10000))
        views = list(
            UserProductView.objects
            .filter(user_id__isnull=False)
            .order_by('-created_at')[:limit]
            .values('user_id', 'product_id', 'session_id', 'source', 'created_at')
        )
        clicks = list(
            UserClickEvent.objects
            .filter(user_id__isnull=False, product_id__isnull=False)
            .order_by('-created_at')[:limit]
            .values('user_id', 'product_id', 'session_id', 'event_type', 'created_at')
        )
        searches = list(
            UserSearchLog.objects
            .filter(user_id__isnull=False)
            .order_by('-created_at')[:5000]
            .values('user_id', 'session_id', 'query', 'results_count', 'created_at')
        )
        return Response({
            'views': views,
            'clicks': clicks,
            'searches': searches,
            'total_views': len(views),
            'total_clicks': len(clicks),
            'total_searches': len(searches),
        })
