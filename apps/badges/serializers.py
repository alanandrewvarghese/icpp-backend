from rest_framework import serializers
from .models import Badge, UserBadge

class BadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for Badge model.
    """
    class Meta:
        model = Badge
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for UserBadge model, including nested Badge details.
    """
    badge = BadgeSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserBadge
        fields = '__all__'
        read_only_fields = ('earned_at',)
