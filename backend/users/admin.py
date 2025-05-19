from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, UserSession, UserDevice, UserActivity, VerificationToken

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_system_role', 'created_at', 'updated_at')
    list_filter = ('is_system_role', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'permissions')
        }),
        (_('Status'), {
            'fields': ('is_system_role',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 
                   'is_verified', 'account_type')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 
                  'account_type', 'language')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions', 'roles')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 
                      'profile_picture', 'bio', 'date_of_birth', 'address',
                      'company', 'position')
        }),
        (_('Account settings'), {
            'fields': ('roles', 'account_type', 'language', 'theme', 'timezone')
        }),
        (_('Security settings'), {
            'fields': ('is_verified', 'is_2fa_enabled', 'failed_login_attempts',
                      'last_failed_login', 'account_locked_until', 
                      'force_password_change')
        }),
        (_('Notification settings'), {
            'fields': ('email_notifications', 'push_notifications',
                      'in_app_notifications', 'notification_preferences')
        }),
        (_('AI settings'), {
            'fields': ('ai_suggestions', 'ai_analysis', 'ai_preferences')
        }),
        (_('Activity tracking'), {
            'fields': ('last_active', 'last_login_ip', 'registration_ip')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                      'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at',
                      'last_active', 'last_login_ip', 'registration_ip',
                      'failed_login_attempts', 'last_failed_login',
                      'account_locked_until')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'browser', 'ip_address', 
                   'is_active', 'last_activity')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'device_name', 'ip_address')
    ordering = ('-last_activity',)
    readonly_fields = ('created_at', 'last_activity')

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'is_trusted', 'last_used')
    list_filter = ('device_type', 'is_trusted', 'created_at')
    search_fields = ('user__username', 'user__email', 'device_name')
    ordering = ('-last_used',)
    readonly_fields = ('device_id', 'created_at', 'last_used')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_type', 'is_used', 'expires_at', 'created_at')
    list_filter = ('token_type', 'is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at')
