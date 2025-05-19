from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization

class Conversation(models.Model):
    class ConversationType(models.TextChoices):
        DIRECT = 'direct', _('Direct Message')
        GROUP = 'group', _('Group Chat')
        CHANNEL = 'channel', _('Channel')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=_('organization')
    )
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT
    )
    
    # For group chats and channels
    name = models.CharField(_('name'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.ImageField(_('icon'), upload_to='conversation_icons/', blank=True, null=True)
    
    # Participants
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ConversationMember',
        related_name='conversations',
        verbose_name=_('participants')
    )
    
    # Settings
    is_archived = models.BooleanField(_('archived'), default=False)
    is_pinned = models.BooleanField(_('pinned'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_conversations',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def __str__(self):
        if self.type == self.ConversationType.DIRECT:
            participants = self.participants.all()[:2]
            return ' & '.join(str(p) for p in participants)
        return self.name

    def add_participant(self, user, role='member'):
        return ConversationMember.objects.create(
            conversation=self,
            user=user,
            role=role
        )

    def remove_participant(self, user):
        return ConversationMember.objects.filter(
            conversation=self,
            user=user
        ).delete()

class ConversationMember(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ADMIN = 'admin', _('Administrator')
        MODERATOR = 'moderator', _('Moderator')
        MEMBER = 'member', _('Member')

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('conversation')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_memberships',
        verbose_name=_('user')
    )
    
    # Role and permissions
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    can_send_messages = models.BooleanField(_('can send messages'), default=True)
    can_add_participants = models.BooleanField(_('can add participants'), default=False)
    can_remove_participants = models.BooleanField(_('can remove participants'), default=False)
    can_manage_settings = models.BooleanField(_('can manage settings'), default=False)
    
    # Notification preferences
    muted_until = models.DateTimeField(_('muted until'), null=True, blank=True)
    desktop_notifications = models.BooleanField(_('desktop notifications'), default=True)
    mobile_notifications = models.BooleanField(_('mobile notifications'), default=True)
    
    # Message tracking
    last_read_at = models.DateTimeField(_('last read at'), null=True, blank=True)
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)

    class Meta:
        verbose_name = _('conversation member')
        verbose_name_plural = _('conversation members')
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user} in {self.conversation}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        verbose_name=_('sender')
    )
    
    # Content
    content = models.TextField(_('content'))
    is_system_message = models.BooleanField(_('system message'), default=False)
    
    # Reply and threading
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('parent message')
    )
    
    # Mentions and reactions
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='message_mentions',
        blank=True,
        verbose_name=_('mentions')
    )
    reactions = models.JSONField(_('reactions'), default=dict)
    
    # Status
    is_edited = models.BooleanField(_('edited'), default=False)
    edited_at = models.DateTimeField(_('edited at'), null=True, blank=True)
    is_deleted = models.BooleanField(_('deleted'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"

class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('message')
    )
    
    # File information
    file = models.FileField(_('file'), upload_to='message_attachments/%Y/%m/%d/')
    file_name = models.CharField(_('file name'), max_length=255)
    file_size = models.BigIntegerField(_('file size'))
    file_type = models.CharField(_('file type'), max_length=100)
    
    # Preview
    thumbnail = models.ImageField(
        _('thumbnail'),
        upload_to='message_attachments/thumbnails/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        verbose_name=_('uploaded by')
    )

    class Meta:
        verbose_name = _('message attachment')
        verbose_name_plural = _('message attachments')
        ordering = ['uploaded_at']

    def __str__(self):
        return self.file_name

    def get_file_extension(self):
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''
