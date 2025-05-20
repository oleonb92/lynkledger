from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    class OrganizationType(models.TextChoices):
        BUSINESS = 'business', _('Business')
        HOUSEHOLD = 'household', _('Household')
        NONPROFIT = 'nonprofit', _('Non-Profit')
        OTHER = 'other', _('Other')

    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_('description'), blank=True)
    organization_type = models.CharField(
        _('organization type'),
        max_length=20,
        choices=OrganizationType.choices,
        default=OrganizationType.BUSINESS
    )
    
    # Branding
    logo = models.ImageField(_('logo'), upload_to='organization_logos/', blank=True, null=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#007bff')
    
    # Contact Information
    email = models.EmailField(_('email'), blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Financial Settings
    fiscal_year_start = models.DateField(_('fiscal year start'), null=True, blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_organizations',
        verbose_name=_('owner')
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='OrganizationMembership',
        through_fields=('organization', 'user'),
        related_name='organizations',
        verbose_name=_('members')
    )

    class Meta:
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_member_count(self):
        return self.members.count()

    def add_member(self, user, role='member'):
        return OrganizationMembership.objects.create(
            organization=self,
            user=user,
            role=role
        )

    def remove_member(self, user):
        return OrganizationMembership.objects.filter(
            organization=self,
            user=user
        ).delete()

class OrganizationMembership(models.Model):
    class RoleChoices(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ADMIN = 'admin', _('Administrator')
        MANAGER = 'manager', _('Manager')
        ACCOUNTANT = 'accountant', _('Accountant')
        BOOKKEEPER = 'bookkeeper', _('Bookkeeper')
        MEMBER = 'member', _('Member')
        VIEWER = 'viewer', _('Viewer')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('organization')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        verbose_name=_('user')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER
    )
    
    # Permissions
    can_manage_members = models.BooleanField(_('can manage members'), default=False)
    can_manage_settings = models.BooleanField(_('can manage settings'), default=False)
    can_manage_billing = models.BooleanField(_('can manage billing'), default=False)
    can_view_reports = models.BooleanField(_('can view reports'), default=True)
    can_create_transactions = models.BooleanField(_('can create transactions'), default=False)
    can_approve_transactions = models.BooleanField(_('can approve transactions'), default=False)
    
    # Metadata
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invites_sent',
        verbose_name=_('invited by')
    )
    invitation_accepted_at = models.DateTimeField(_('invitation accepted at'), null=True, blank=True)
    last_active_at = models.DateTimeField(_('last active at'), auto_now=True)

    class Meta:
        verbose_name = _('organization membership')
        verbose_name_plural = _('organization memberships')
        unique_together = ('organization', 'user')
        ordering = ['organization', 'user']

    def __str__(self):
        return f"{self.user} - {self.organization} ({self.role})"

    def set_role(self, role):
        if role in dict(self.RoleChoices.choices):
            self.role = role
            self.save(update_fields=['role'])
            
    def update_permissions(self, permissions_dict):
        for permission, value in permissions_dict.items():
            if hasattr(self, permission):
                setattr(self, permission, value)
        self.save()

    def has_permission(self, permission):
        return getattr(self, permission, False)
