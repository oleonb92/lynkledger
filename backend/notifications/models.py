from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from organizations.models import Organization

class NotificationCategory(models.Model):
    class CategoryType(models.TextChoices):
        SYSTEM = 'system', _('System')
        ACCOUNT = 'account', _('Account')
        TRANSACTION = 'transaction', _('Transaction')
        DOCUMENT = 'document', _('Document')
        MESSAGE = 'message', _('Message')
        TASK = 'task', _('Task')
        AI = 'ai', _('AI Assistant')
        SECURITY = 'security', _('Security')

    name = models.CharField(_('name'), max_length=100)
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=CategoryType.choices,
        default=CategoryType.SYSTEM
    )
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    color = models.CharField(_('color'), max_length=7, default='#000000')

    class Meta:
        verbose_name = _('notification category')
        verbose_name_plural = _('notification categories')
        ordering = ['name']

    def __str__(self):
        return self.name

class NotificationTemplate(models.Model):
    class TemplateType(models.TextChoices):
        EMAIL = 'email', _('Email')
        PUSH = 'push', _('Push Notification')
        IN_APP = 'in_app', _('In-App Notification')
        SMS = 'sms', _('SMS')

    category = models.ForeignKey(
        NotificationCategory,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name=_('category')
    )
    name = models.CharField(_('name'), max_length=255)
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=TemplateType.choices
    )
    
    # Template content
    subject = models.CharField(_('subject'), max_length=255)
    body = models.TextField(_('body'))
    
    # Optional HTML version for emails
    html_body = models.TextField(_('HTML body'), blank=True)
    
    # Template variables
    variables = models.JSONField(_('variables'), default=list)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('notification template')
        verbose_name_plural = _('notification templates')
        unique_together = ('category', 'type', 'name')

    def __str__(self):
        return f"{self.category} - {self.name} ({self.type})"

class Notification(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        NORMAL = 'normal', _('Normal')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        READ = 'read', _('Read')
        FAILED = 'failed', _('Failed')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('organization')
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('recipient')
    )
    category = models.ForeignKey(
        NotificationCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notifications',
        verbose_name=_('category')
    )
    
    # Notification content
    title = models.CharField(_('title'), max_length=255)
    message = models.TextField(_('message'))
    data = models.JSONField(_('data'), default=dict, blank=True)
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status and tracking
    priority = models.CharField(
        _('priority'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Delivery channels
    email_sent = models.BooleanField(_('email sent'), default=False)
    push_sent = models.BooleanField(_('push sent'), default=False)
    sms_sent = models.BooleanField(_('SMS sent'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)
    scheduled_for = models.DateTimeField(_('scheduled for'), null=True, blank=True)
    
    # Actions
    actions = models.JSONField(_('actions'), default=list, blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.title}"

    def mark_as_read(self):
        from django.utils import timezone
        self.status = self.Status.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])

    def mark_as_sent(self, channel=None):
        if channel == 'email':
            self.email_sent = True
        elif channel == 'push':
            self.push_sent = True
        elif channel == 'sms':
            self.sms_sent = True
            
        if all([self.email_sent, self.push_sent, self.sms_sent]):
            self.status = self.Status.SENT
            
        self.save()

class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('user')
    )
    category = models.ForeignKey(
        NotificationCategory,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('category')
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(_('email enabled'), default=True)
    push_enabled = models.BooleanField(_('push enabled'), default=True)
    sms_enabled = models.BooleanField(_('SMS enabled'), default=False)
    
    # Quiet hours
    quiet_hours_start = models.TimeField(_('quiet hours start'), null=True, blank=True)
    quiet_hours_end = models.TimeField(_('quiet hours end'), null=True, blank=True)
    
    # Frequency settings
    min_interval = models.DurationField(_('minimum interval'), null=True, blank=True)
    daily_limit = models.PositiveIntegerField(_('daily limit'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user} - {self.category}"

    def can_send_notification(self, channel='email'):
        """Check if a notification can be sent based on preferences and limits"""
        if channel == 'email':
            return self.email_enabled
        elif channel == 'push':
            return self.push_enabled
        elif channel == 'sms':
            return self.sms_enabled
        return False
