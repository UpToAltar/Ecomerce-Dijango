from domain.models import User


class AuthService:
    """Domain service for authentication logic."""

    @staticmethod
    def register_customer(email, password, first_name, last_name, **kwargs):
        """Register a new customer account."""
        if User.objects.filter(email=email).exists():
            raise ValueError('Email already exists')
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.CUSTOMER,
            **kwargs,
        )
        return user

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_profile(user, **kwargs):
        """Update user profile fields."""
        allowed_fields = ['first_name', 'last_name', 'phone', 'address']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    def list_users(role=None):
        """List users, optionally filtered by role."""
        qs = User.objects.all()
        if role:
            qs = qs.filter(role=role)
        return qs
