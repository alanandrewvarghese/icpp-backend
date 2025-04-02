from rest_framework import serializers
from .models import LessonProgress, ExerciseSubmission
from apps.lessons.models import Exercise

class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for LessonProgress model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LessonProgress
        fields = '__all__'
        read_only_fields = ('completed_at',)


class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for ExerciseSubmission model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(queryset = Exercise.objects.all())
    execution_result = serializers.PrimaryKeyRelatedField(queryset = 'apps.sandbox.models.ExecutionResult', allow_null=True, required=False)
    submitted_code = serializers.CharField(required=True)

    class Meta:
        model = ExerciseSubmission
        fields = '__all__'
        read_only_fields = ('submitted_at', 'is_correct')


class LessonProgressPercentageSerializer(serializers.Serializer):
    """
    Serializer for lesson progress percentage data.
    """
    lesson_id = serializers.IntegerField()
    lesson_title = serializers.CharField()
    progress_percentage = serializers.FloatField()
    completed_exercises = serializers.IntegerField()
    total_exercises = serializers.IntegerField()
    is_completed = serializers.BooleanField()
