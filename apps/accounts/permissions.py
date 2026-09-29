from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """Allows access only to users with the ADMIN role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_role)

class IsStudentRole(permissions.BasePermission):
    """Allows access only to users with the STUDENT role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)

class IsOwnerOrAdmin(permissions.BasePermission):
    """Object-level permission to only allow owners of an object or admins to view/edit it."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role:
            return True
        return hasattr(obj, 'user') and obj.user == request.user
