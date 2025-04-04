from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BadgeViewSet, UserBadgeListView

router = DefaultRouter()
router.register(r'badges', BadgeViewSet, basename='badge')

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/badges/', UserBadgeListView.as_view(), name='user-badges-list')
]
