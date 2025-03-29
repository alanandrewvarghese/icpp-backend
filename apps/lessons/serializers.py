from rest_framework import serializers
from .models import Lesson, Exercise

class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = '__all__'  # Include all fields from the Lesson model
        read_only_fields = ('created_by','created_by_name')  # Make created_by read-only in updates

    def get_created_by_name(self, obj):
      return obj.created_by.username if obj.created_by else None



class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for Exercise model."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = '__all__' # Include all fields from the Exercise model
        read_only_fields = ('created_by','author_name') # Make created_by read-only in updates

    def get_author_name(self, obj):
      return obj.created_by.username if obj.created_by else None


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for listing Lesson model -  can customize fields for list view."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title','description', 'order','author_name') # Example: Just title and order for list view

    def get_author_name(self, obj):
      return obj.created_by.username if obj.created_by else None



class ExerciseListSerializer(serializers.ModelSerializer):
    """Serializer for listing Exercise model - can customize fields for list view."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ('id', 'title', 'lesson','description','author_name') # Example: Just title and lesson for list view

    def get_author_name(self, obj):
      return obj.created_by.username if obj.created_by else None


class LessonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Lesson model - can customize fields for creation if needed."""
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'description', 'content', 'order') # Example: Fields required for creation


class ExerciseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Exercise model - can customize fields for creation if needed."""
    class Meta:
        model = Exercise
        fields = ('lesson', 'title', 'description', 'starter_code', 'solution_code', 'test_cases') # Example: Fields for exercise creation


class LessonUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Lesson model -  can customize fields for updates."""
    class Meta:
        model = Lesson
        fields = ('title', 'description', 'content') # Example:  Fields allowed for update
        read_only_fields = ('created_by',) # Ensure created_by cannot be updated directly


class ExerciseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Exercise model - can customize fields for updates."""
    class Meta:
        model = Exercise
        fields = ('lesson', 'title', 'description', 'starter_code', 'solution_code', 'test_cases') # Example: Fields allowed for update
        read_only_fields = ('created_by',) # Ensure created_by cannot be updated directly
