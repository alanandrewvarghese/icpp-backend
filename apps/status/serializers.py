from rest_framework import serializers
from .models import CompletionStatus

class CompletionStatusSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = CompletionStatus
        fields = ['id', 'user', 'username', 'content_type', 'content_id', 'completed', 'completed_at']
        read_only_fields = ['completed_at']

    def get_username(self, obj):
        return obj.user.username if obj.user else None

class StatusUpdateSerializer(serializers.Serializer):
    completed = serializers.BooleanField(required=True)
