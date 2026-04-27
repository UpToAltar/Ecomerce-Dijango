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
    CreateStaffSerializer,
)
from .permissions import IsAdmin, IsStaffOrAdmin


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


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/auth/users/<id>/ — Manage a user (admin only)."""
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    lookup_field = 'id'


class CreateStaffView(APIView):
    """POST /api/auth/users/create-staff/ — Admin creates a staff user."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CreateStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        if User.objects.filter(email=d['email']).exists():
            return Response({'error': 'Email already exists'}, status=400)
        user = User.objects.create_user(
            email=d['email'],
            password=d['password'],
            first_name=d.get('first_name', ''),
            last_name=d.get('last_name', ''),
            phone=d.get('phone', ''),
            role=User.Role.STAFF,
            is_staff=True,
        )
        return Response(UserAdminSerializer(user).data, status=201)


class UpdateUserStatusView(APIView):
    """PUT /api/auth/users/<id>/status/ — Activate or deactivate user."""
    permission_classes = [IsAdmin]

    def put(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'error': 'is_active required'}, status=400)
        user.is_active = bool(is_active)
        user.save(update_fields=['is_active'])
        return Response(UserAdminSerializer(user).data)


class AdminUserStatsView(APIView):
    """GET /api/auth/users/stats/ — User counts by role."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import Count
        counts = User.objects.values('role').annotate(count=Count('id'))
        result = {item['role']: item['count'] for item in counts}
        return Response({
            'total': User.objects.count(),
            'by_role': result,
        })


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
