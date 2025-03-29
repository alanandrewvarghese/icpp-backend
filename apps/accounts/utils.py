from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse
import logging

logger = logging.getLogger("accounts")
User = get_user_model()


def send_password_reset_email(request, user):
    """
    Utility function to send a password reset email to a user.

    Args:
        request: The Django request object (needed to build absolute URI).
        user: The User object to send the reset email to.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    try:
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = reverse('auth-password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
        absolute_reset_url = request.build_absolute_uri(reset_url)
        frontend_reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"
        print(frontend_reset_url)

        # Send password reset email
        mail_subject = 'Password Reset Request'

        message = render_to_string('reset_email.html',{
            'user': user,
            'reset_url': absolute_reset_url,
            'frontend_reset_url': frontend_reset_url,
        })

        send_mail(
            mail_subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to: {user.email}")
        return True  # Email sent successfully
    except Exception as e:
        logger.exception(f"Error sending password reset email to {user.email}: {e}")
        return False # Email sending failed


def confirm_password_reset(uidb64, token, new_password):
    """
    Utility function to confirm password reset using token and set new password.

    Args:
        uidb64: Base64 encoded user ID from the URL.
        token: Password reset token from the URL.
        new_password: The new password to set.

    Returns:
        tuple: (user, success, message)
               - user: User object if password reset is successful, None otherwise.
               - success: Boolean, True if password reset is successful, False otherwise.
               - message: String, success or error message.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        logger.warning(f"Invalid uidb64 during password reset confirmation: {uidb64}")
        return None, False, "Invalid or expired reset token."

    if user is not None and default_token_generator.check_token(user, token):
        try:
            user.set_password(new_password)
            user.save()
            logger.info(f"Password successfully reset for user: {user.username}")
            return user, True, "Password reset successfully."
        except Exception as e:
            logger.exception(f"Error setting new password during reset for user: {user.username}: {e}")
            return None, False, "Password reset failed."
    else:
        logger.warning(f"Invalid password reset token for user: {user.username if user else 'unknown user'}, uidb64: {uidb64}, token: {token}")
        return None, False, "Invalid or expired reset token."



def username_or_email_exists(username,email):
    if User.objects.filter(username=username).exists():
        logger.error(f"Account creation failed: Username '{username}' already exists.")
        return True
    if User.objects.filter(email=email).exists():
        logger.error(f"Account creation failed: Email id '{email}' already exists.")
        return True
    return False

def create_superuser_admin_account(username, email, password, role='admin'):
    """
    Creates an admin account with the role of 'admin' and superuser privileges.
    """
    try:
        if username_or_email_exists(username,email):
            return None
        user = User.objects.create_superuser(username=username, email=email, password=password)
        user.role = 'admin'
        user.save()
        logger.info(f"Admin account '{username}' created successfully.")
        return user
    except Exception as e:
        logger.error(f"Error at create_superuser_admin_account: {e}")
        return None

def create_instructor_account(username, email, password):
    """
    Creates an instructor account with the role of 'instructor' and normal user privileges.
    """
    try:
        if username_or_email_exists(username,email):
            return None
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = 'instructor'
        user.is_active = False
        user.save()
        logger.info(f"Instructor account '{username}' created successfully.")
        return user
    except Exception as e:
        logger.error(f"Error at create_instructor_account: {e}")
        return None

def create_student_account(username, email, password):
    """
    Creates a student account with the role of 'student' and normal user privileges.
    """
    try:
        if username_or_email_exists(username,email):
            return None
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = 'student'
        user.save()
        logger.info(f"Student account '{username}' created successfully.")
        return user
    except Exception as e:
        logger.error(f"Error at create_student_account: {e}")
        return None
