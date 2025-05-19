from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class LanguageChoices(models.TextChoices):
        ENGLISH = 'en', _('English')
        SPANISH = 'es', _('Spanish')

    class ThemeChoices(models.TextChoices):
        LIGHT = 'light', _('Light')
        DARK = 'dark', _('Dark')
        SYSTEM = 'system', _('System')

    # Profile fields
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    profile_picture = models.ImageField(_('profile picture'), upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(_('biography'), blank=True)
    
    # Preferences
    language = models.CharField(
        _('language'),
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH
    )
    theme = models.CharField(
        _('theme'),
        max_length=10,
        choices=ThemeChoices.choices,
        default=ThemeChoices.SYSTEM
    )
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    
    # Notification preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    in_app_notifications = models.BooleanField(_('in-app notifications'), default=True)
    
    # AI preferences
    ai_suggestions = models.BooleanField(_('AI suggestions'), default=True)
    ai_analysis = models.BooleanField(_('AI analysis'), default=True)
    
    # Account status
    is_verified = models.BooleanField(_('verified'), default=False)
    account_type = models.CharField(_('account type'), max_length=20, default='personal')
    last_active = models.DateTimeField(_('last active'), auto_now=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    def __str__(self):
        return self.email or self.username
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_notification_settings(self):
        return {
            'email': self.email_notifications,
            'push': self.push_notifications,
            'in_app': self.in_app_notifications
        }
    
    def get_ai_settings(self):
        return {
            'suggestions': self.ai_suggestions,
            'analysis': self.ai_analysis
        }
    
    def toggle_notification_setting(self, notification_type):
        if hasattr(self, f'{notification_type}_notifications'):
            setattr(self, f'{notification_type}_notifications', 
                   not getattr(self, f'{notification_type}_notifications'))
            self.save(update_fields=[f'{notification_type}_notifications'])
            
    def toggle_ai_setting(self, setting_type):
        if hasattr(self, f'ai_{setting_type}'):
            setattr(self, f'ai_{setting_type}', 
                   not getattr(self, f'ai_{setting_type}'))
            self.save(update_fields=[f'ai_{setting_type}'])
