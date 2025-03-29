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
    UserListView,
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    InstructorListView,
    StudentListView,
    InstructorApproveAPIView,
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


    # User management
    path('admin/users/', UserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/detail/', UserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:pk>/update/', UserUpdateView.as_view(), name='admin-user-update'),
    path('admin/users/<int:pk>/delete/', UserDeleteView.as_view(), name='admin-user-delete'),

    # Admin - List Instructors and Students
    path('admin/users/instructors/', InstructorListView.as_view(), name='admin-instructor-list'),
    path('admin/users/students/', StudentListView.as_view(), name='admin-student-list'),

    # Admin - Approve Instructor
    path('admin/instructors/<int:pk>/approve/', InstructorApproveAPIView.as_view(), name='admin-instructor-approve'),
]
