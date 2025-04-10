from rest_framework import serializers
from .models import SupportTicket, TicketResponse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data within ticket and response serializers."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = fields


class TicketResponseSerializer(serializers.ModelSerializer):
    """Serializer for ticket responses."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = TicketResponse
        fields = ('id', 'ticket', 'user', 'message', 'created_at', 'is_admin_response')
        read_only_fields = ('id', 'user', 'created_at', 'is_admin_response')


class TicketResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new responses."""
    class Meta:
        model = TicketResponse
        fields = ('message',)


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets with responses included."""
    user = UserSerializer(read_only=True)
    responses = TicketResponseSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)

    class Meta:
        model = SupportTicket
        fields = ('id', 'title', 'description', 'user', 'created_at', 'updated_at',
                  'status', 'status_display', 'ticket_type', 'ticket_type_display',
                  'related_lesson', 'related_exercise', 'responses')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new support tickets."""
    class Meta:
        model = SupportTicket
        fields = ('title', 'description', 'ticket_type', 'related_lesson', 'related_exercise')


class SupportTicketListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing tickets without responses."""
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    response_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = ('id', 'title', 'user', 'created_at', 'updated_at',
                  'status', 'status_display', 'ticket_type', 'ticket_type_display',
                  'response_count')

    def get_response_count(self, obj):
        return obj.responses.count()
