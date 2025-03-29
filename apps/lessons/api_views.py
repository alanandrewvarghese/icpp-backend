from rest_framework import viewsets, permissions, serializers, status
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Lesson, Exercise
from django.db.models import Max
from .serializers import (
    LessonCreateSerializer,
    LessonSerializer,
    LessonListSerializer,
    ExerciseCreateSerializer,
    ExerciseListSerializer,
    ExerciseSerializer,
    LessonUpdateSerializer,
    ExerciseUpdateSerializer,
)
from apps.common.permissions import IsAdminOrInstructor, IsAdmin # Import custom permissions


logger = logging.getLogger("lessons") # Get logger for this module

class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Lesson model.
    """
    queryset = Lesson.objects.all().order_by('order') # Retrieve all lessons, ordered by 'order' field
    serializer_class = LessonSerializer

    def get_permissions(self):
        """
        Determine permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrInstructor] # Admin or Instructor can modify
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated] # Student, Instructor, Admin can read
        else:
            permission_classes = [IsAdmin] # Admin for other actions if any.
        return [permission() for permission in permission_classes]


    def get_serializer_class(self):
        """
        Override method to use different serializers for different actions.
        """
        if self.action == 'list':
            return LessonListSerializer
        elif self.action == 'create':
            return LessonCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return LessonUpdateSerializer
        return LessonSerializer

    def perform_create(self, serializer):
        """
        Automatically set the creator to the current user.
        """
        try:
            serializer.save(created_by=self.request.user)
            logger.info(f"Lesson '{serializer.validated_data.get('title')}' created by user '{self.request.user.username}'.")
        except Exception as e:
            logger.error(f"Error creating lesson '{serializer.validated_data.get('title')}' by user '{self.request.user.username}': {e}")


class ExerciseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Exercise model.
    """
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

    def get_permissions(self):
        """
        Determine permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrInstructor] # Admin or Instructor can modify
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated] # Student, Instructor, Admin can read
        else:
            permission_classes = [IsAdmin] # Admin for other actions if any.
        return [permission() for permission in permission_classes]


    def get_serializer_class(self):
        """
        Override method to use different serializers for different actions.
        """
        if self.action == 'list':
            return ExerciseListSerializer
        elif self.action == 'create':
            return ExerciseCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ExerciseUpdateSerializer
        return ExerciseSerializer

    def perform_create(self, serializer):
        """
        Override method to ensure lesson and creator are correctly set during exercise creation.
        """
        try:
            lesson_id = self.request.data.get('lesson') # Assuming lesson is passed in request data
            lesson = Lesson.objects.get(pk=lesson_id)
            serializer.save(lesson=lesson, created_by=self.request.user) # Set lesson and creator
            logger.info(f"Exercise '{serializer.validated_data.get('title')}' created in lesson '{lesson.title}' by user '{self.request.user.username}'.")
        except serializers.ValidationError as e:
            logger.warning(f"Validation error creating exercise '{serializer.validated_data.get('title')}' by user '{self.request.user.username}': {e}")
            raise e # Re-raise validation error to be handled by DRF
        except Lesson.DoesNotExist:
            raise serializers.ValidationError({"lesson": "Invalid lesson ID."})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])  # Anyone authenticated can read
def lesson_exercises_list(request, lesson_id):
    """
    List exercises for a specific lesson.
    """
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        logger.warning(f"lesson_exercises_list: Lesson with ID '{lesson_id}' not found.")
        return Response({"error": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND)

    exercises = lesson.exercises.all()
    serializer = ExerciseListSerializer(exercises, many=True) # Serialize multiple exercises
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def lesson_max_order(request):
    """
    Returns the maximum order value from existing lessons.
    If no lessons exist, returns 0.
    """
    try:
        max_order = Lesson.objects.all().aggregate(Max('order'))['order__max']
        result = max_order or 0  # Use 0 if max_order is None (no lessons exist)
        return Response({"max_order": result}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error retrieving maximum lesson order: {e}")
        return Response(
            {"error": "Failed to retrieve max order"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
