from rest_framework import serializers
from .models import Lesson, Exercise

class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""
    class Meta:
        model = Lesson
        fields = '__all__' # Include all fields from the Lesson model
        read_only_fields = ('created_by',) # Make created_by read-only in updates


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model."""
    class Meta:
        model = Exercise
        fields = '__all__' # Include all fields from the Exercise model
        read_only_fields = ('created_by',) # Make created_by read-only in updates


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for listing Lesson model -  can customize fields for list view."""
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'order') # Example: Just title and order for list view


class ExerciseListSerializer(serializers.ModelSerializer):
    """Serializer for listing Exercise model - can customize fields for list view."""
    class Meta:
        model = Exercise
        fields = ('id', 'title', 'lesson') # Example: Just title and lesson for list view


class LessonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Lesson model - can customize fields for creation if needed."""
    class Meta:
        model = Lesson
        fields = ('title', 'description', 'content', 'order') # Example: Fields required for creation


class ExerciseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Exercise model - can customize fields for creation if needed."""
    class Meta:
        model = Exercise
        fields = ('lesson', 'title', 'description', 'starter_code', 'solution_code', 'test_cases') # Example: Fields for exercise creation


class LessonUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Lesson model -  can customize fields for updates."""
    class Meta:
        model = Lesson
        fields = ('title', 'description', 'content', 'order') # Example:  Fields allowed for update
        read_only_fields = ('created_by',) # Ensure created_by cannot be updated directly


class ExerciseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Exercise model - can customize fields for updates."""
    class Meta:
        model = Exercise
        fields = ('lesson', 'title', 'description', 'starter_code', 'solution_code', 'test_cases') # Example: Fields allowed for update
        read_only_fields = ('created_by',) # Ensure created_by cannot be updated directly