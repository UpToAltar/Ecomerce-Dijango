from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
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
