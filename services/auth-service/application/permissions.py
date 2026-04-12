from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allows access only to admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsStaffOrAdmin(BasePermission):
    """Allows access to staff and admin users."""
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
            and request.user.role in ('admin', 'staff')
        )


class IsOwnerOrAdmin(BasePermission):
    """Allows access to the owner of the object or admin users."""
    def has_object_permission(self, request, view, obj):
        return request.user.role == 'admin' or obj.id == request.user.id
