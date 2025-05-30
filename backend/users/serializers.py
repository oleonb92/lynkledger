from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Role
from organizations.models import Organization, OrganizationMembership, OrganizationInvitation
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    organization_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password',
                 'first_name', 'last_name', 'phone_number', 'language',
                 'timezone', 'account_type', 'organization_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(_("Passwords don't match"))
        return data

    def create(self, validated_data):
        request = self.context.get('request', None)
        invitation_token = None
        if request:
            invitation_token = request.data.get('invitation_token')
        organization_name = validated_data.pop('organization_name')
        validated_data.pop('confirm_password')
        
        if invitation_token:
            # Registro por invitación: asociar a la organización de la invitación
            try:
                invitation = OrganizationInvitation.objects.get(token=invitation_token, status=OrganizationInvitation.StatusChoices.PENDING)
            except OrganizationInvitation.DoesNotExist:
                raise serializers.ValidationError({'invitation_token': _('Invalid or expired invitation token.')})
            # Usar el email de la invitación como email y username
            invitation_email = invitation.email
            validated_data['email'] = invitation_email
            validated_data['username'] = invitation_email
            # Validar que no exista usuario con ese email o username
            if User.objects.filter(email=invitation_email).exists() or User.objects.filter(username=invitation_email).exists():
                raise serializers.ValidationError({'email': _('A user with this email already exists. Please log in instead.')})
            user = User.objects.create_user(**validated_data)
            # Marcar usuario como verificado
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            # Asociar usuario a la organización
            OrganizationMembership.objects.create(
                organization=invitation.organization,
                user=user,
                role=invitation.role,
                invited_by=invitation.invited_by,
                invitation_accepted_at=timezone.now(),
                can_manage_members=False,
                can_manage_settings=False,
                can_manage_billing=False,
                can_view_reports=True,
                can_create_transactions=True,
                can_approve_transactions=False
            )
            # Marcar invitación como aceptada
            invitation.accepted_at = timezone.now()
            invitation.accepted_by = user
            invitation.status = OrganizationInvitation.StatusChoices.ACCEPTED
            invitation.save()
            return user
        else:
            # Registro normal: crear organización
            base_slug = slugify(organization_name)
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            try:
                user = User.objects.create_user(**validated_data)
                organization = Organization.objects.create(
                    name=organization_name,
                    slug=slug,
                    owner=user,
                    organization_type='business'  # Default type
                )
            except Exception as e:
                raise serializers.ValidationError({
                    'organization_name': _('An organization with this name already exists. Please choose another name.')
                })
            OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role='owner',
                can_manage_members=True,
                can_manage_settings=True,
                can_manage_billing=True,
                can_view_reports=True,
                can_create_transactions=True,
                can_approve_transactions=True
            )
            return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                 'phone_number', 'profile_picture', 'bio', 'language',
                 'theme', 'timezone', 'account_type', 'is_verified',
                 'email_notifications', 'push_notifications',
                 'in_app_notifications', 'ai_suggestions', 'ai_analysis',
                 'last_active', 'date_joined')
        read_only_fields = ('id', 'is_verified', 'last_active', 'date_joined')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError(_("New passwords don't match"))
        return data

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in Permission model"""
    content_type = serializers.CharField(source='content_type.model')
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Permission.objects.all(),
        required=False,
        source='permissions'
    )
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions', 
            'permission_ids', 'is_system_role', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_system_role', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate that the role name is unique and follows conventions"""
        # Convert to lowercase and replace spaces with underscores
        value = value.lower().replace(' ', '_')
        
        # Check if role with this name already exists
        if Role.objects.filter(name=value).exists():
            if self.instance and self.instance.name == value:
                return value
            raise serializers.ValidationError("A role with this name already exists.")
        
        return value

    def create(self, validated_data):
        """Create a new role with permissions"""
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        if permissions:
            role.permissions.set(permissions)
        return role

    def update(self, instance, validated_data):
        """Update an existing role"""
        permissions = validated_data.pop('permissions', None)
        
        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permissions is not None:
            instance.permissions.set(permissions)
        
        return instance 

class UserMeSerializer(serializers.ModelSerializer):
    organization_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'organization_id']

    def get_organization_id(self, obj):
        membership = OrganizationMembership.objects.filter(user=obj).first()
        if membership:
            return membership.organization.id
        return None 