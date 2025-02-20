from rest_framework import serializers

class SuccessResponseSerializer(serializers.Serializer):
    """
    Generic serializer for success responses with a message.
    """
    message = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    """
    Generic serializer for error responses with an error message.
    """
    error = serializers.CharField()