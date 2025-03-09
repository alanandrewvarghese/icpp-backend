from rest_framework import serializers
from .models import LessonProgress, ExerciseSubmission # Import the models we created
from apps.lessons.models import Exercise

class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for LessonProgress model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True) # Display user ID, make it read-only

    class Meta:
        model = LessonProgress # Tell serializer which model to use
        fields = '__all__' # Include all fields from the LessonProgress model
        read_only_fields = ('completed_at',) # 'completed_at' is automatically set, so it's read-only for updates


class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for ExerciseSubmission model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True) # Make user read-only
    exercise = serializers.PrimaryKeyRelatedField(queryset = Exercise.objects.all())
    execution_result = serializers.PrimaryKeyRelatedField(queryset = 'apps.sandbox.models.ExecutionResult', allow_null=True, required=False) # Optional execution result
    submitted_code = serializers.CharField(required=True)

    class Meta:
        model = ExerciseSubmission # Tell serializer which model to use
        fields = '__all__' # Include all fields
        read_only_fields = ('submitted_at', 'is_correct') # These fields are set automatically or determined by backend