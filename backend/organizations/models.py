from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import stripe
from datetime import timedelta

User = get_user_model()

class Organization(models.Model):
    """
    Modelo que representa una organización en el sistema.
    
    Una organización puede tener múltiples miembros y un propietario.
    También puede tener un patrocinador (sponsor) que puede ser un contador o un cliente.
    """
    class OrganizationType(models.TextChoices):
        BUSINESS = 'business', _('Business')
        HOUSEHOLD = 'household', _('Household')
        NONPROFIT = 'nonprofit', _('Non-Profit')
        OTHER = 'other', _('Other')

    class PlanType(models.TextChoices):
        FREE = 'free', _('Free')
        PRO = 'pro', _('Professional')
        ENTERPRISE = 'enterprise', _('Enterprise')

    name = models.CharField(_("Nombre"), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_("Descripción"), blank=True)
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
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Última actualización"), auto_now=True)
    is_active = models.BooleanField(_("Activa"), default=True)
    
    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_organizations',
        verbose_name=_("Propietario")
    )
    members = models.ManyToManyField(
        User,
        through='OrganizationMembership',
        through_fields=('organization', 'user'),
        related_name='organizations',
        verbose_name=_("Miembros")
    )

    # Subscription and Billing
    plan = models.CharField(
        _('plan'),
        max_length=32,
        choices=PlanType.choices,
        default=PlanType.FREE
    )
    sponsor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sponsored_organizations',
        verbose_name=_("Patrocinador")
    )
    sponsor_type = models.CharField(
        _("Tipo de Patrocinador"),
        max_length=20,
        choices=[
            ('accountant', _('Contador')),
            ('client', _('Cliente'))
        ],
        default='client'
    )
    stripe_customer_id = models.CharField(
        _("ID de Cliente Stripe"),
        max_length=255,
        blank=True,
        null=True
    )
    subscription_status = models.CharField(
        _("Estado de Suscripción"),
        max_length=50,
        choices=[
            ('inactive', _('Inactiva')),
            ('active', _('Activa')),
            ('past_due', _('Pago Pendiente')),
            ('canceled', _('Cancelada')),
            ('trialing', _('En Período de Prueba'))
        ],
        default='inactive'
    )
    subscription_end_date = models.DateTimeField(
        _("Fecha de Fin de Suscripción"),
        null=True,
        blank=True
    )
    trial_ends_at = models.DateTimeField(
        _('trial ends at'),
        null=True,
        blank=True
    )
    accountant_incentive_granted = models.BooleanField(
        _('accountant incentive granted'),
        default=False
    )

    class Meta:
        verbose_name = _("Organización")
        verbose_name_plural = _("Organizaciones")
        ordering = ['-created_at']

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

    def transfer_sponsorship(self, new_sponsor, sponsor_type='client'):
        """
        Transfiere el patrocinio de la organización a otro usuario.
        
        Args:
            new_sponsor: El nuevo usuario patrocinador
            sponsor_type: El tipo de patrocinador ('accountant' o 'client')
        """
        if sponsor_type == 'accountant' and not new_sponsor.groups.filter(name='accountants').exists():
            raise ValidationError(_("El nuevo patrocinador debe ser un contador."))
        
        self.sponsor = new_sponsor
        self.sponsor_type = sponsor_type
        self.save()

    def sponsor_must_pay(self):
        """Determina si el sponsor actual debe pagar la suscripción."""
        if not self.sponsor:
            return False
            
        if self.plan == self.PlanType.FREE:
            return False
            
        if self.sponsor_type == 'accountant':
            # El contador siempre paga por sus funcionalidades pro
            return True
            
        # Si el cliente es el sponsor, paga por el plan de la organización
        return self.plan in [self.PlanType.PRO, self.PlanType.ENTERPRISE]

    def is_in_trial(self):
        """Verifica si la organización está en período de prueba."""
        if not self.trial_ends_at:
            return False
        return timezone.now() < self.trial_ends_at

    def grant_accountant_incentive(self):
        """Otorga un incentivo al contador sponsor."""
        if not self.sponsor or self.sponsor_type != 'accountant':
            return False
            
        if self.accountant_incentive_granted:
            return False
            
        incentive = Incentive.objects.create(
            user=self.sponsor,
            organization=self,
            type='free_month',
            status='granted'
        )
        
        self.accountant_incentive_granted = True
        self.save()
        
        # TODO: Enviar notificación al contador
        return incentive

    def update_all_members_pro_features(self):
        """Actualiza el acceso pro de todas las membresías de la organización."""
        for membership in self.memberships.all():
            membership.update_pro_features()

    def clean(self):
        if self.sponsor and self.sponsor_type == 'accountant':
            if not self.sponsor.groups.filter(name='accountants').exists():
                raise ValidationError(_("El patrocinador debe ser un contador."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def check_subscription_status(self):
        """
        Verifica el estado actual de la suscripción.
        
        Returns:
            bool: True si la suscripción está activa, False en caso contrario
        """
        if not self.stripe_customer_id:
            return False
        
        try:
            customer = stripe.Customer.retrieve(self.stripe_customer_id)
            subscriptions = stripe.Subscription.list(customer=customer.id)
            
            if not subscriptions.data:
                self.subscription_status = 'inactive'
                self.save()
                return False
            
            subscription = subscriptions.data[0]
            self.subscription_status = subscription.status
            
            if subscription.current_period_end:
                self.subscription_end_date = timezone.datetime.fromtimestamp(
                    subscription.current_period_end,
                    tz=timezone.utc
                )
            
            self.save()
            return subscription.status == 'active'
            
        except stripe.error.StripeError:
            return False

class OrganizationMembership(models.Model):
    """
    Modelo que representa la membresía de un usuario en una organización.
    
    Define el rol y los permisos que tiene un usuario dentro de una organización.
    """
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
        verbose_name=_("Organización")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        verbose_name=_("Usuario")
    )
    role = models.CharField(
        _("Rol"),
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
    
    # Pro Features
    pro_features_enabled = models.BooleanField(_('pro features enabled'), default=False)
    pro_features_source = models.CharField(
        _('pro features source'),
        max_length=32,
        choices=[
            ('accountant_subscription', 'Accountant Subscription'),
            ('organization_plan', 'Organization Plan'),
            ('trial', 'Trial Period')
        ],
        null=True,
        blank=True
    )
    pro_features_for_accountant = models.BooleanField(_('pro features for accountant'), default=False)
    
    # Metadata
    joined_at = models.DateTimeField(_("Fecha de ingreso"), auto_now_add=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invites_sent',
        verbose_name=_('invited by')
    )
    invitation_accepted_at = models.DateTimeField(_('invitation accepted at'), null=True, blank=True)
    last_active_at = models.DateTimeField(_('last active at'), auto_now=True)
    is_active = models.BooleanField(_("Activo"), default=True)

    class Meta:
        verbose_name = _("Membresía de Organización")
        verbose_name_plural = _("Membresías de Organizaciones")
        unique_together = ['organization', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"

    def clean(self):
        if self.role == self.RoleChoices.OWNER and self.organization.owner != self.user:
            raise ValidationError(_("Solo el propietario puede tener el rol de owner."))

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

    def update_pro_features(self):
        """Actualiza el estado de las características pro basado en el plan de la organización y el rol."""
        if self.role == self.RoleChoices.ACCOUNTANT:
            # Los contadores siempre tienen acceso pro si la organización es pro
            # o si tienen su propia suscripción pro
            self.pro_features_enabled = (
                self.organization.plan in [Organization.PlanType.PRO, Organization.PlanType.ENTERPRISE] or
                self.user.has_pro_subscription()
            )
            self.pro_features_source = (
                'organization_plan' if self.organization.plan in [Organization.PlanType.PRO, Organization.PlanType.ENTERPRISE]
                else 'accountant_subscription' if self.user.has_pro_subscription()
                else None
            )
        else:
            # Para otros roles, depende del plan de la organización
            self.pro_features_enabled = self.organization.plan in [Organization.PlanType.PRO, Organization.PlanType.ENTERPRISE]
            self.pro_features_source = 'organization_plan' if self.pro_features_enabled else None

        self.save(update_fields=['pro_features_enabled', 'pro_features_source'])

    def has_pro_access(self):
        """Verifica si el miembro tiene acceso a características pro."""
        if self.organization.is_in_trial():
            return True
        return self.pro_features_enabled

class OrganizationInvitation(models.Model):
    """
    Modelo que representa una invitación para unirse a una organización.
    
    Permite invitar a usuarios a unirse a una organización con un rol específico.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACCEPTED = 'accepted', _('Accepted')
        DECLINED = 'declined', _('Declined')
        EXPIRED = 'expired', _('Expired')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_("Organización")
    )
    email = models.EmailField(_("Email"))
    role = models.CharField(
        _("Rol"),
        max_length=20,
        choices=OrganizationMembership.RoleChoices.choices,
        default=OrganizationMembership.RoleChoices.MEMBER
    )
    message = models.TextField(_('message'), blank=True)
    token = models.CharField(_("Token"), max_length=100, unique=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Fecha de expiración"))
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organization_invitations_sent',
        verbose_name=_('invited by')
    )
    accepted_at = models.DateTimeField(_('accepted at'), null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organization_invitations_accepted',
        verbose_name=_('accepted by')
    )

    class Meta:
        verbose_name = _("Invitación a Organización")
        verbose_name_plural = _("Invitaciones a Organizaciones")
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.organization.name} for {self.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        """
        Verifica si la invitación ha expirado.
        
        Returns:
            bool: True si la invitación ha expirado, False en caso contrario
        """
        return timezone.now() > self.expires_at

    def accept(self, user):
        if self.status != self.StatusChoices.PENDING:
            return False
        
        self.status = self.StatusChoices.ACCEPTED
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save()

        # Create membership
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=user,
            role=self.role,
            invited_by=self.invited_by,
            invitation_accepted_at=self.accepted_at
        )
        return membership

    def decline(self):
        if self.status != self.StatusChoices.PENDING:
            return False
        
        self.status = self.StatusChoices.DECLINED
        self.save()
        return True

    def expire(self):
        if self.status == self.StatusChoices.PENDING:
            self.status = self.StatusChoices.EXPIRED
            self.save()
            return True
        return False

class Incentive(models.Model):
    """
    Modelo que representa un incentivo para usuarios.
    
    Los incentivos pueden ser descuentos, períodos de prueba extendidos,
    o otras promociones para usuarios.
    """
    class IncentiveType(models.TextChoices):
        FREE_MONTH = 'free_month', _('Free Month')
        DISCOUNT = 'discount', _('Discount')
        CREDIT = 'credit', _('Credit')
        FEATURE_UNLOCK = 'feature_unlock', _('Feature Unlock')

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending')
        GRANTED = 'granted', _('Granted')
        USED = 'used', _('Used')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incentives',
        verbose_name=_("Usuario")
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='incentives',
        verbose_name=_('organization')
    )
    type = models.CharField(
        _("Tipo"),
        max_length=50,
        choices=IncentiveType.choices
    )
    status = models.CharField(
        _('status'),
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    value = models.DecimalField(
        _("Valor"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    description = models.TextField(
        _('description'),
        blank=True
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    granted_at = models.DateTimeField(
        _('granted at'),
        null=True,
        blank=True
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        null=True,
        blank=True
    )
    used_at = models.DateTimeField(
        _('used at'),
        null=True,
        blank=True
    )
    is_used = models.BooleanField(_("Usado"), default=False)

    class Meta:
        verbose_name = _("Incentivo")
        verbose_name_plural = _("Incentivos")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} for {self.user.email}"

    def grant(self):
        """Otorga el incentivo al usuario."""
        if self.status != self.StatusChoices.PENDING:
            return False
        self.status = self.StatusChoices.GRANTED
        self.granted_at = timezone.now()
        self.save()
        # TODO: Enviar notificación al usuario
        return True

    def expire(self):
        """Marca el incentivo como expirado."""
        if self.status not in [self.StatusChoices.PENDING, self.StatusChoices.GRANTED]:
            return False
        self.status = self.StatusChoices.EXPIRED
        self.save()
        # TODO: Enviar notificación al usuario
        return True

    def cancel(self):
        """Cancela el incentivo."""
        if self.status not in [self.StatusChoices.PENDING, self.StatusChoices.GRANTED]:
            return False
        self.status = self.StatusChoices.CANCELLED
        self.save()
        # TODO: Enviar notificación al usuario
        return True

    def is_valid(self):
        """
        Verifica si el incentivo es válido (no expirado y no usado).
        
        Returns:
            bool: True si el incentivo es válido, False en caso contrario
        """
        if self.is_used:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.expire()
            return False
        return True
