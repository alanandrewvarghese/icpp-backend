from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import CompletionStatus
from .serializers import CompletionStatusSerializer, StatusUpdateSerializer
import logging

logger = logging.getLogger("status")

class CompletionStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for managing completion statuses"""
    serializer_class = CompletionStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter statuses to only show the current user's data"""
        return CompletionStatus.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Ensure user is set to the current user when creating a status"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def lessons(self, request):
        """Get all lesson completion statuses for current user"""
        queryset = self.get_queryset().filter(content_type='lesson')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def quizzes(self, request):
        """Get all quiz completion statuses for current user"""
        queryset = self.get_queryset().filter(content_type='quiz')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def exercises(self, request):
        """Get all exercise completion statuses for current user"""
        queryset = self.get_queryset().filter(content_type='exercise')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContentStatusView(APIView):
    """API view to get or update status for a specific content item"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, content_type, content_id):
        """Get status for a specific content item"""
        if content_type not in ['lesson', 'quiz', 'exercise']:
            return Response({"error": "Invalid content type"}, status=status.HTTP_400_BAD_REQUEST)

        status_obj, created = CompletionStatus.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            content_id=content_id,
            defaults={'completed': False}
        )

        serializer = CompletionStatusSerializer(status_obj)
        return Response(serializer.data)

    def put(self, request, content_type, content_id):
        """Update status for a specific content item"""
        if content_type not in ['lesson', 'quiz', 'exercise']:
            return Response({"error": "Invalid content type"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        status_obj, created = CompletionStatus.objects.update_or_create(
            user=request.user,
            content_type=content_type,
            content_id=content_id,
            defaults={'completed': serializer.validated_data['completed']}
        )

        logger.info(f"User {request.user.username} marked {content_type} {content_id} as {'completed' if status_obj.completed else 'incomplete'}")
        response_serializer = CompletionStatusSerializer(status_obj)
        return Response(response_serializer.data)
