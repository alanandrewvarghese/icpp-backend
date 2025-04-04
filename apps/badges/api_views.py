from rest_framework import viewsets, permissions, generics
from .models import Badge, UserBadge
from .serializers import BadgeSerializer, UserBadgeSerializer
from apps.common.permissions import IsAdmin

class BadgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Badge model.
    Accessible only to admin users.
    """
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [IsAdmin]


class UserBadgeListView(generics.ListAPIView):
    """
    API view to list badges earned by the currently authenticated user.
    """
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter badges to only show those earned by the current user.
        """
        return UserBadge.objects.filter(user=self.request.user).select_related('badge')


# Optional: If you want to manage UserBadges via API as well (e.g., admin awarding, listing all user badges)
# class UserBadgeViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet for CRUD operations on UserBadge model.
#     Accessible only to admin users.
#     """
#     queryset = UserBadge.objects.all()
#     serializer_class = UserBadgeSerializer
#     permission_classes = [IsAdmin] # Restrict access to admin users only
