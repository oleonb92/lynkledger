from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.conf import settings
import pyotp
import uuid
from datetime import datetime, timedelta
import json

def get_default_notification_preferences():
    return {}

def get_default_ai_preferences():
    return {}

class Role(models.Model):
    """Custom role model for fine-grained permissions"""
    name = models.CharField(_('name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True
    )
    is_system_role = models.BooleanField(_('system role'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self):
        return self.name

class User(AbstractUser):
    class LanguageChoices(models.TextChoices):
        ENGLISH = 'en', _('English')
        SPANISH = 'es', _('Spanish')

    class ThemeChoices(models.TextChoices):
        LIGHT = 'light', _('Light')
        DARK = 'dark', _('Dark')
        SYSTEM = 'system', _('System')

    class AccountType(models.TextChoices):
        PERSONAL = 'personal', _('Personal')
        BUSINESS = 'business', _('Business')
        ACCOUNTANT = 'accountant', _('Accountant')
        ADMIN = 'admin', _('Administrator')

    # Override username field with custom validator
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    # Basic Fields
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        blank=True
    )

    # Profile Fields
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/%Y/%m/',
        blank=True,
        null=True
    )
    bio = models.TextField(_('biography'), blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    address = models.TextField(_('address'), blank=True)
    company = models.CharField(_('company'), max_length=255, blank=True)
    position = models.CharField(_('position'), max_length=255, blank=True)

    # Account Settings
    roles = models.ManyToManyField(
        Role,
        verbose_name=_('roles'),
        blank=True,
        related_name='users'
    )
    account_type = models.CharField(
        _('account type'),
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.PERSONAL
    )
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

    # Security Settings
    is_verified = models.BooleanField(_('email verified'), default=False)
    is_2fa_enabled = models.BooleanField(_('2FA enabled'), default=False)
    twofa_secret = models.CharField(max_length=32, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(auto_now_add=True, null=True)
    force_password_change = models.BooleanField(default=False)

    # Notification Preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    in_app_notifications = models.BooleanField(_('in-app notifications'), default=True)
    _notification_preferences = models.TextField(
        _('notification preferences'),
        blank=True,
        null=True,
        db_column='notification_preferences'
    )

    # AI Preferences
    ai_suggestions = models.BooleanField(_('AI suggestions'), default=True)
    ai_analysis = models.BooleanField(_('AI analysis'), default=True)
    _ai_preferences = models.TextField(
        _('AI preferences'),
        blank=True,
        null=True,
        db_column='ai_preferences'
    )

    # Activity Tracking
    last_active = models.DateTimeField(_('last active'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # New fields for professional features and Stripe customer ID
    pro_features = models.BooleanField(_('pro features'), default=False)
    stripe_customer_id = models.CharField(_('stripe customer id'), max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email or self.username

    @property
    def notification_preferences(self):
        if not self._notification_preferences:
            return {}
        return json.loads(self._notification_preferences)

    @notification_preferences.setter
    def notification_preferences(self, value):
        if value is None:
            self._notification_preferences = None
        else:
            self._notification_preferences = json.dumps(value)

    @property
    def ai_preferences(self):
        if not self._ai_preferences:
            return {}
        return json.loads(self._ai_preferences)

    @ai_preferences.setter
    def ai_preferences(self, value):
        if value is None:
            self._ai_preferences = None
        else:
            self._ai_preferences = json.dumps(value)

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def generate_2fa_secret(self):
        """Generate a new 2FA secret key"""
        self.twofa_secret = pyotp.random_base32()
        self.save(update_fields=['twofa_secret'])
        return self.twofa_secret

    def verify_2fa_code(self, code):
        """Verify a 2FA code"""
        if not self.twofa_secret:
            return False
        totp = pyotp.TOTP(self.twofa_secret)
        return totp.verify(code)

    def get_2fa_qr_url(self):
        """Get the QR code URL for 2FA setup"""
        if not self.twofa_secret:
            return None
        totp = pyotp.TOTP(self.twofa_secret)
        return totp.provisioning_uri(self.email, issuer_name="Lynkledger")

    def record_login_attempt(self, success, ip_address=None):
        """Record a login attempt"""
        if success:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.account_locked_until = None
            self.last_login_ip = ip_address
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = timezone.now()
            if self.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                self.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=[
            'failed_login_attempts',
            'last_failed_login',
            'account_locked_until',
            'last_login_ip'
        ])

    def is_account_locked(self):
        """Check if the account is locked"""
        if not self.account_locked_until:
            return False
        return timezone.now() < self.account_locked_until

    def get_notification_settings(self):
        """Get all notification settings"""
        base_settings = {
            'email': self.email_notifications,
            'push': self.push_notifications,
            'in_app': self.in_app_notifications
        }
        return {**base_settings, **self.notification_preferences}

    def get_ai_settings(self):
        """Get all AI settings"""
        base_settings = {
            'suggestions': self.ai_suggestions,
            'analysis': self.ai_analysis
        }
        return {**base_settings, **self.ai_preferences}

    def update_notification_preferences(self, preferences):
        """Update notification preferences"""
        current_prefs = self.notification_preferences
        current_prefs.update(preferences)
        self.notification_preferences = current_prefs
        self.save(update_fields=['_notification_preferences'])

    def update_ai_preferences(self, preferences):
        """Update AI preferences"""
        current_prefs = self.ai_preferences
        current_prefs.update(preferences)
        self.ai_preferences = current_prefs
        self.save(update_fields=['_ai_preferences'])

class UserSession(models.Model):
    """Model to track user sessions"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=40, unique=True)
    device_type = models.CharField(max_length=50, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.email} - {self.device_type} - {self.created_at}"

class UserDevice(models.Model):
    """Model to track user devices"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)
    push_token = models.CharField(max_length=255, blank=True)
    is_trusted = models.BooleanField(default=False)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user device')
        verbose_name_plural = _('user devices')
        ordering = ['-last_used']

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"

class UserActivity(models.Model):
    """Model to track user activity"""
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        SETTINGS_CHANGE = 'settings_change', _('Settings Change')
        SECURITY_CHANGE = 'security_change', _('Security Change')
        OTHER = 'other', _('Other')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.ForeignKey(
        UserDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"

class VerificationToken(models.Model):
    """Model for email verification and password reset tokens"""
    class TokenType(models.TextChoices):
        EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
        DEVICE_VERIFICATION = 'device_verification', _('Device Verification')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    token_type = models.CharField(
        max_length=50,
        choices=TokenType.choices
    )
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('verification token')
        verbose_name_plural = _('verification tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.token_type} - {self.created_at}"

    def is_valid(self):
        """Check if the token is valid"""
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_token(cls, user, token_type, expiry_hours=24):
        """Generate a new token"""
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        return cls.objects.create(
            user=user,
            token_type=token_type,
            expires_at=expires_at
        )
