from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.contrib.auth import update_session_auth_hash, authenticate
from django.db.models import Q
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import logging
import os

from .utils import ( 
    create_instructor_account,
    create_student_account,
    create_superuser_admin_account,
    send_password_reset_email,
    confirm_password_reset,
)

from .serializers import (
    SuccessResponseSerializer,
    ErrorResponseSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    ReadOnlyUserSerializer,
    InstructorRegistrationSerializer,
    StudentRegistrationSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

load_dotenv()

logger = logging.getLogger("accounts")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

class AdminInitAPIView(APIView):
    """
    API view to initialize the superuser admin account.
    This should ideally be run only once during setup.
    """
    permission_classes = [AllowAny]

    
    def get(self, request):
        try:
            User = get_user_model()

            if not ADMIN_USERNAME or not ADMIN_EMAIL or not ADMIN_PASSWORD:
                logger.error("Admin account initialization failed: Missing admin credentials in environment variables.")
                return Response({"error": "Admin account initialization failed. Missing admin credentials."}, status=500)

            if User.objects.filter(Q(username=ADMIN_USERNAME) | Q(email=ADMIN_EMAIL)).exists():
                logger.info("Admin user already exists. Initialization skipped.")
                return Response({"message": "Admin user already exists."}, status=200)

            admin_user = create_superuser_admin_account(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
            if admin_user:
                logger.info(f"Admin account '{ADMIN_USERNAME}' initialized successfully.")
                return Response({"message": "Admin account initialization successful."}, status=201)
            else:
                logger.error("Admin account initialization failed: create_superuser_admin_account returned None.")
                return Response({"error": "Admin account initialization failed."}, status=500)

        except Exception as e:
            logger.exception(f"Error during admin account initialization: {e}")
            return Response({"error": f"Admin account initialization failed: {e}"}, status=500)
        


class LoginAPIView(APIView):
    """
    API view for user login using JWT authentication.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        request_serializer = LoginRequestSerializer(data=request.data)

        if request_serializer.is_valid():
            username = request_serializer.validated_data['username']
            password = request_serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)

                user_serializer = ReadOnlyUserSerializer(user)
                response_data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": user_serializer.data,
                }

                response_serializer = LoginResponseSerializer(data=response_data)
                if response_serializer.is_valid(): 
                    logger.info(f"User '{username}' logged in successfully.")
                    return Response(response_serializer.data, status=200)
                else:
                    logger.error(f"Login response serialization error: {response_serializer.errors}")
                    return Response({"error": "Internal server error during response serialization."}, status=500)

        return Response(request_serializer.errors, status=400)  

    
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the token

            # Optionally, delete all outstanding tokens for added security
            # This might not be needed in all cases, but enhances security against token reuse
            #all_outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
            #all_outstanding_tokens.delete()

            logger.info(f"User '{request.user.username}' logged out successfully.")
            return Response({"message": "Successfully logged out."}, status=200)

        except TokenError as e:
            logger.warning(f"Logout failed for user '{request.user.username}': {e}")
            return Response({"error": "Invalid token."}, status=400)
        except Exception as e:
            logger.exception(f"An unexpected error occurred during logout: {e}")
            return Response({"error": "Logout failed."}, status=500)
        


class InstructorRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_serializer = InstructorRegistrationSerializer(data=request.data)

        if request_serializer.is_valid(): # Validate request data
            username = request_serializer.validated_data['username']
            email = request_serializer.validated_data['email']
            password = request_serializer.validated_data['password']

            instructor = create_instructor_account(username, email, password)

            if instructor is not None:
                success_serializer = SuccessResponseSerializer(data={"message": "Instructor account created successfully."})
                success_serializer.is_valid(raise_exception=True)
                logger.info(f"Instructor account '{username}' created successfully.")
                return Response(success_serializer.data, status=201)
            else:
                error_serializer = ErrorResponseSerializer(data={"error": "Account creation failed.  Username or email may already exist."})
                error_serializer.is_valid(raise_exception=True)
                return Response(error_serializer.data, status=400)
        else:
            return Response(request_serializer.errors, status=400)
    


class StudentRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_serializer = StudentRegistrationSerializer(data=request.data)
        if request_serializer.is_valid():
            username = request_serializer.validated_data['username']
            email = request_serializer.validated_data['email']
            password = request_serializer.validated_data['password']

            student = create_student_account(username, email, password)

            if student is not None:
                success_serializer = SuccessResponseSerializer(data={"message": "Student account created successfully."})
                success_serializer.is_valid(raise_exception=True)
                logger.info(f"Student account '{username}' created successfully.")
                return Response(success_serializer.data, status=201)
            else:
                error_serializer = ErrorResponseSerializer(data={"error": "Account creation failed.  Username or email may already exist."})
                error_serializer.is_valid(raise_exception=True)
                return Response(error_serializer.data, status=400)
        else:
            return Response(request_serializer.errors, status=400)
    


class ChangePasswordAPIView(APIView):
    """
    API view to allow authenticated users to change their password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_serializer = ChangePasswordSerializer(data=request.data)

        if request_serializer.is_valid():
            old_password = request_serializer.validated_data['oldpassword']
            new_password = request_serializer.validated_data['newpassword']
            confirm_new_password = request_serializer.validated_data['confirmnewpassword']

            user = authenticate(request, username=request.user.username, password=old_password)

            if user is None:
                error_serializer = ErrorResponseSerializer(data={"error": "Incorrect old password."})
                error_serializer.is_valid(raise_exception=True)
                logger.warning(f"Password change attempt by user '{request.user.username}' - incorrect old password.")
                return Response(error_serializer.data, status=400)

            if new_password == old_password:
                error_serializer = ErrorResponseSerializer(data={"error": "New password cannot be the same as the old password."})
                error_serializer.is_valid(raise_exception=True)
                logger.warning(f"Password change attempt by user '{request.user.username}' - new password is the same as old password.")
                return Response(error_serializer.data, status=400)

            try:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  
                success_serializer = SuccessResponseSerializer(data={"message": "Password changed successfully."}) 
                success_serializer.is_valid(raise_exception=True)
                logger.info(f"Password successfully changed for user '{request.user.username}'.")
                return Response(success_serializer.data, status=200) 

            except Exception as e:
                error_serializer = ErrorResponseSerializer(data={"error": "Failed to change password."}) 
                error_serializer.is_valid(raise_exception=True)
                logger.exception(f"Error while changing password for user '{request.user.username}': {e}")
                return Response(error_serializer.data, status=500) 
        else:
            return Response(request_serializer.errors, status=400) 
        


class PasswordResetRequestAPIView(APIView):
    """
    API view to request a password reset email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        request_serializer = PasswordResetRequestSerializer(data=request.data)
        if request_serializer.is_valid():
            email = request_serializer.validated_data['email']

            User = get_user_model()
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"Password reset requested for non-existent email: {email}")
                success_serializer = SuccessResponseSerializer(data={"message": "Password reset email sent if the email is registered."}) 
                success_serializer.is_valid(raise_exception=True)
                return Response(success_serializer.data, status=200)

            email_sent = send_password_reset_email(request, user)

            if email_sent:
                success_serializer = SuccessResponseSerializer(data={"message": "Password reset email sent if the email is registered."}) 
                success_serializer.is_valid(raise_exception=True)
                return Response(success_serializer.data, status=200) 
            else:
                error_serializer = ErrorResponseSerializer(data={"error": "Error sending password reset email."}) 
                error_serializer.is_valid(raise_exception=True)
                return Response(error_serializer.data, status=500) 

        else:
            return Response(request_serializer.errors, status=400)

        


class PasswordResetConfirmAPIView(APIView):
    """
    API view to confirm password reset using token and set new password.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        request_serializer = PasswordResetConfirmSerializer(data=request.data)

        if request_serializer.is_valid():
            new_password = request_serializer.validated_data['new_password'] 
            confirm_new_password = request_serializer.validated_data['confirm_new_password']

            user, success, message = confirm_password_reset(uidb64, token, new_password) 

            if success:
                success_serializer = SuccessResponseSerializer(data={"message": message}) 
                success_serializer.is_valid(raise_exception=True)
                return Response(success_serializer.data, status=200) 
            else:
                error_serializer = ErrorResponseSerializer(data={"error": message}) 
                error_serializer.is_valid(raise_exception=True)
                return Response(error_serializer.data, status=400) 

        else:
            return Response(request_serializer.errors, status=400) 