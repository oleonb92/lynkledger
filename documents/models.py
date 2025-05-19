from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization

class DocumentCategory(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='document_categories',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent category')
    )
    
    # UI/UX
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    color = models.CharField(_('color'), max_length=7, default='#000000')
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_document_categories',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('document category')
        verbose_name_plural = _('document categories')
        unique_together = ('organization', 'name', 'parent')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Get the full category path (e.g., 'Invoices/2023/Q1')"""
        path = [self.name]
        current = self.parent
        while current:
            path.append(current.name)
            current = current.parent
        return ' / '.join(reversed(path))

class Document(models.Model):
    class DocumentType(models.TextChoices):
        INVOICE = 'invoice', _('Invoice')
        RECEIPT = 'receipt', _('Receipt')
        CONTRACT = 'contract', _('Contract')
        REPORT = 'report', _('Report')
        TAX = 'tax', _('Tax Document')
        OTHER = 'other', _('Other')

    class DocumentStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ARCHIVED = 'archived', _('Archived')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('organization')
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents',
        verbose_name=_('category')
    )
    
    # Basic information
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    document_type = models.CharField(
        _('document type'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    
    # File handling
    file = models.FileField(_('file'), upload_to='documents/%Y/%m/%d/')
    file_size = models.BigIntegerField(_('file size'), default=0)
    file_type = models.CharField(_('file type'), max_length=50, blank=True)
    original_filename = models.CharField(_('original filename'), max_length=255)
    
    # OCR and content
    ocr_content = models.TextField(_('OCR content'), blank=True)
    is_ocr_processed = models.BooleanField(_('OCR processed'), default=False)
    
    # Status and workflow
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.DRAFT
    )
    
    # Dates
    document_date = models.DateField(_('document date'), null=True, blank=True)
    due_date = models.DateField(_('due date'), null=True, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    
    # Tags and metadata
    tags = models.JSONField(_('tags'), default=list, blank=True)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Access control
    is_private = models.BooleanField(_('private'), default=False)
    is_template = models.BooleanField(_('template'), default=False)
    
    # Relationships
    related_documents = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name=_('related documents')
    )
    
    # Audit trail
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents',
        verbose_name=_('created by')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_documents',
        verbose_name=_('approved by')
    )

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_file_extension(self):
        return self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''

    def get_sharing_info(self):
        return {
            'shared_with': self.shares.values_list('user__email', flat=True),
            'public_link': self.public_shares.filter(is_active=True).first()
        }

class DocumentShare(models.Model):
    class Permission(models.TextChoices):
        VIEW = 'view', _('View')
        COMMENT = 'comment', _('Comment')
        EDIT = 'edit', _('Edit')
        MANAGE = 'manage', _('Manage')

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_('document')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_documents',
        verbose_name=_('user')
    )
    
    # Permissions
    permission = models.CharField(
        _('permission'),
        max_length=20,
        choices=Permission.choices,
        default=Permission.VIEW
    )
    
    # Share settings
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_shares_created',
        verbose_name=_('created by')
    )
    
    class Meta:
        verbose_name = _('document share')
        verbose_name_plural = _('document shares')
        unique_together = ('document', 'user')

    def __str__(self):
        return f"{self.document} - {self.user} ({self.permission})"

class DocumentComment(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('document')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_comments',
        verbose_name=_('user')
    )
    
    content = models.TextField(_('content'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('parent comment')
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_edited = models.BooleanField(_('edited'), default=False)
    
    class Meta:
        verbose_name = _('document comment')
        verbose_name_plural = _('document comments')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} on {self.document} - {self.content[:50]}"

class PublicShare(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='public_shares',
        verbose_name=_('document')
    )
    
    # Share settings
    token = models.CharField(_('token'), max_length=64, unique=True)
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    requires_password = models.BooleanField(_('requires password'), default=False)
    password_hash = models.CharField(_('password hash'), max_length=128, blank=True)
    
    # Access tracking
    access_count = models.IntegerField(_('access count'), default=0)
    last_accessed = models.DateTimeField(_('last accessed'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='public_shares_created',
        verbose_name=_('created by')
    )
    
    class Meta:
        verbose_name = _('public share')
        verbose_name_plural = _('public shares')

    def __str__(self):
        return f"Public share for {self.document}"

    def get_absolute_url(self):
        return f"/documents/share/{self.token}/"
