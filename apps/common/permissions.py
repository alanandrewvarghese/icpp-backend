from rest_framework import permissions

class IsAdminOrInstructor(permissions.BasePermission):
    """
    Custom permission to allow only admins or instructors to access.
    """

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) in ["admin", "instructor"]


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to allow only admin to access.
    """

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "admin"


class IsInstructor(permissions.BasePermission):
    """
    Custom permission to allow only instructors to access.
    """

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "instructor"


class IsStudent(permissions.BasePermission):
    """
    Custom permission to allow only students to access.
    """

    def has_permission(self, request, view):
        return getattr(request.user, "role", None) == "student"
