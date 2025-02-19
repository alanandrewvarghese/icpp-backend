from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import (
    LoginAPIView,
    InstructorRegistrationAPIView,
    StudentRegistrationAPIView,
    LogoutAPIView,
    AdminInitAPIView,
    ChangePasswordAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,
)

urlpatterns = [
    # Initialize admin account
    path('admin/init/', AdminInitAPIView.as_view(), name="admin-init"),
    

    # Authentication
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/password/change/", ChangePasswordAPIView.as_view(), name="auth-password-change"),
    path("auth/password/reset/", PasswordResetRequestAPIView.as_view(), name="auth-password-reset"),
    path('auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmAPIView.as_view(), name='auth-password-reset-confirm'),


    # Registraton endpoints
    path("register/instructor/", InstructorRegistrationAPIView.as_view(), name="register-instructor"),
    path("register/student/", StudentRegistrationAPIView.as_view(), name="register-student"),
]