from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings

def send_plan_change_email(user, organization, old_plan, new_plan):
    context = {
        'user': user,
        'organization': organization,
        'old_plan': old_plan,
        'new_plan': new_plan,
        'frontend_url': settings.FRONTEND_URL,
        'year': timezone.now().year,
    }
    html_message = render_to_string('notifications/email/plan_change.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Tu organización '{organization.name}' cambió de plan: {old_plan} → {new_plan}",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_incentive_granted_email(user, organization, incentive):
    context = {
        'user': user,
        'organization': organization,
        'incentive': incentive,
        'frontend_url': settings.FRONTEND_URL,
        'year': timezone.now().year,
    }
    html_message = render_to_string('notifications/email/incentive_granted.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"¡Has recibido un incentivo en {organization.name}!",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    ) 