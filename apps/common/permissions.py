from rest_framework import permissions

class IsAdminOrInstructor(permissions.BasePermission):
    """
    Custom permission to allow only admins or instructors to access and modify.
    Instructors can only modify their own resources.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ["admin", "instructor"]

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.role == 'admin':
            return True

        # Instructor can perform actions on their own lessons/exercises
        if request.user.role == 'instructor':
            if hasattr(obj, 'created_by'): # Check if object has 'created_by' attribute
                return obj.created_by == request.user

        return False # Default deny for other cases or missing 'created_by'


class IsAdmin(permissions.BasePermission):
    """Custom permission to allow only admin to access."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "admin"


class IsInstructor(permissions.BasePermission):
    """Custom permission to allow only instructors to access."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "instructor"


class IsStudent(permissions.BasePermission):
    """Custom permission to allow only students to access."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "student"