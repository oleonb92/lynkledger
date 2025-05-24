from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Organization, OrganizationMembership, OrganizationInvitation, Incentive

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'owner', 'member_count', 'is_active', 'created_at')
    list_filter = ('organization_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'email', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('owner',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'organization_type', 'owner')
        }),
        (_('Branding'), {
            'fields': ('logo', 'primary_color'),
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone', 'address', 'website'),
        }),
        (_('Financial Settings'), {
            'fields': ('fiscal_year_start', 'currency', 'tax_id'),
        }),
        (_('Status'), {
            'fields': ('is_active', 'created_at', 'updated_at'),
        }),
    )

    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = _('Members')

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'joined_at', 'last_active_at')
    list_filter = ('role', 'joined_at', 'organization')
    search_fields = ('user__email', 'organization__name')
    raw_id_fields = ('user', 'organization', 'invited_by')
    readonly_fields = ('joined_at', 'invitation_accepted_at', 'last_active_at')

    fieldsets = (
        (None, {
            'fields': ('organization', 'user', 'role')
        }),
        (_('Permissions'), {
            'fields': (
                'can_manage_members',
                'can_manage_settings',
                'can_manage_billing',
                'can_view_reports',
                'can_create_transactions',
                'can_approve_transactions'
            ),
        }),
        (_('Invitation Details'), {
            'fields': ('invited_by', 'joined_at', 'invitation_accepted_at', 'last_active_at'),
        }),
    )

@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'role', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'role', 'created_at')
    search_fields = ('email', 'organization__name', 'invited_by__email')
    raw_id_fields = ('organization', 'invited_by', 'accepted_by')
    readonly_fields = ('token', 'created_at', 'expires_at', 'accepted_at')

    fieldsets = (
        (None, {
            'fields': ('organization', 'email', 'role', 'message')
        }),
        (_('Status Information'), {
            'fields': ('status', 'token', 'created_at', 'expires_at'),
        }),
        (_('Acceptance Details'), {
            'fields': ('accepted_at', 'accepted_by'),
        }),
    )

    def has_change_permission(self, request, obj=None):
        if obj and obj.status != 'pending':
            return False
        return super().has_change_permission(request, obj)

admin.site.register(Incentive)
