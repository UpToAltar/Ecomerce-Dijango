from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from domain.models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserAdminSerializer,
)
from .permissions import IsAdmin


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Register a new customer."""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'Registration successful',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — Login and get JWT tokens."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RefreshTokenView(TokenRefreshView):
    """POST /api/auth/refresh/ — Refresh access token."""
    permission_classes = [AllowAny]


class ProfileView(APIView):
    """GET/PUT /api/auth/profile/ — View or update own profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UserListView(generics.ListAPIView):
    """GET /api/auth/users/ — List all users (admin only)."""
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class UserDetailView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/auth/users/<id>/ — Manage a user (admin only)."""
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    lookup_field = 'id'


class ValidateTokenView(APIView):
    """GET /api/auth/validate/ — Validate JWT token (used by gateway)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user': {
                'id': str(request.user.id),
                'email': request.user.email,
                'role': request.user.role,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            },
        })
