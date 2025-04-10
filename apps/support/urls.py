from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import SupportTicketViewSet, AdminTicketViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='support-ticket')
router.register(r'admin/tickets', AdminTicketViewSet, basename='admin-ticket')

urlpatterns = [
    path('', include(router.urls)),
]
