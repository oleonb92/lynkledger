from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

@shared_task
def send_welcome_email(user_email, username):
    """
    Envía un email de bienvenida a un nuevo usuario.
    """
    subject = '¡Bienvenido a LynkLedger!'
    html_message = render_to_string('users/email/welcome.html', {
        'username': username,
        'login_url': f"{settings.SITE_URL}/login",
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )

@shared_task
def send_password_reset_email(user_email, reset_token):
    """
    Envía un email para restablecer la contraseña.
    """
    subject = 'Restablecimiento de contraseña - LynkLedger'
    reset_url = f"{settings.SITE_URL}/reset-password/{reset_token}"
    
    html_message = render_to_string('users/email/password_reset.html', {
        'reset_url': reset_url,
        'expiry_hours': 24,
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )

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