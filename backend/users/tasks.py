from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

@shared_task
def send_verification_email(user_id, token):
    """Send email verification link to user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user,
            'verification_url': f"{settings.FRONTEND_URL}/verify-email/{token}"
        }
        html_message = render_to_string('users/email/verification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Verify your email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False

@shared_task
def send_password_reset_email(user_id, token):
    """Send password reset link to user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user,
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{token}"
        }
        html_message = render_to_string('users/email/password_reset.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Reset your password',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False

@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user."""
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user,
            'login_url': f"{settings.FRONTEND_URL}/login"
        }
        html_message = render_to_string('users/email/welcome.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Welcome to LynkLedger!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message
        )
        return True
    except User.DoesNotExist:
        return False

@shared_task
def send_notification_email(user_email, subject, message):
    """
    Envía una notificación por email.
    """
    html_message = render_to_string('users/email/notification.html', {
        'message': message,
        'timestamp': timezone.now(),
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    ) 