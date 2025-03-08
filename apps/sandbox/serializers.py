from rest_framework import serializers
from .models import ExecutionRequest, ExecutionResult

class ExecutionRequestSerializer(serializers.ModelSerializer):
    """Serializer for ExecutionRequest model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True) # Display user ID, make it read-only
    exercise = serializers.PrimaryKeyRelatedField(queryset = 'apps.lessons.models.Exercise', allow_null=True) # Allow null for optional exercise
    status = serializers.CharField(read_only=True) # Status should be set server-side, read-only
    stdin = serializers.CharField(required=False, allow_blank=True, default='')
    args = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = ExecutionRequest
        fields = ['id', 'user', 'exercise', 'code', 'sandbox', 'created_at', 'status', 'stdin', 'args']
        read_only_fields = ['id', 'created_at', 'status', 'user']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set queryset for exercise to avoid import issues at module level
        from apps.lessons.models import Exercise # Import locally to avoid circular imports
        self.fields['exercise'].queryset = Exercise.objects.all()


class ExecutionResultSerializer(serializers.ModelSerializer):
    """Serializer for ExecutionResult model."""
    request = serializers.PrimaryKeyRelatedField(read_only=True) # Make request read-only

    class Meta:
        model = ExecutionResult
        # MODIFIED: Added 'test_results' to the fields list
        fields = ['id', 'request', 'output', 'error', 'execution_time', 'test_results']
        read_only_fields = ['id', 'request'] # request is set when creating result