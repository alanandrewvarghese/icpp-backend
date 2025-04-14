from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CompletionStatusViewSet, ContentStatusView

router = DefaultRouter()
router.register(r'statuses', CompletionStatusViewSet, basename='completion-status')

urlpatterns = [
    path('', include(router.urls)),
    path('<str:content_type>/<int:content_id>/', ContentStatusView.as_view(), name='content-status'),
]
