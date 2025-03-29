from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ReadOnlyUserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model to represent user details in responses.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'registration_date','is_active')
        read_only_fields = fields


class LoginRequestSerializer(serializers.Serializer):
    """
    Serializer for Login API request data.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for Login API response data.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = serializers.DictField() # Nested serializer for user details


class InstructorRegistrationSerializer(serializers.Serializer):
    """
    Serializer for Instructor Registration API request data.
    """
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True) # write_only to not include password in response


class StudentRegistrationSerializer(serializers.Serializer):
    """
    Serializer for Student Registration API request data.
    """
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True) # write_only to not include password in response


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for Change Password API request data.
    """
    oldpassword = serializers.CharField(required=True, write_only=True)
    newpassword = serializers.CharField(required=True, write_only=True)
    confirmnewpassword = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Check that newpassword and confirmnewpassword match.
        """
        if data['newpassword'] != data['confirmnewpassword']:
            raise serializers.ValidationError("New passwords do not match.")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for Password Reset Request API data.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for Password Reset Confirm API data.
    """
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """
        Check that new_password and confirm_new_password match.
        """
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing User model in admin user management.
    Includes fields suitable for a user list view.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'registration_date', 'is_active')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating User model by administrators.
    Allows updating specific fields like role and is_active.
    """
    class Meta:
        model = User
        fields = ('email','is_active','role',)

class InstructorApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approving instructor accounts by administrators.
    Allows updating is_active status to True.
    """
    class Meta:
        model = User
        fields = ('is_active',)
