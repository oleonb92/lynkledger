from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Organization, OrganizationMembership, OrganizationInvitation, Incentive
from datetime import timedelta
from django.utils import timezone

class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='get_member_count', read_only=True)
    is_owner = serializers.SerializerMethodField()
    current_user_role = serializers.SerializerMethodField()
    is_sponsor = serializers.SerializerMethodField()
    can_start_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'organization_type',
            'logo', 'primary_color', 'email', 'phone', 'address',
            'website', 'fiscal_year_start', 'currency', 'tax_id',
            'created_at', 'updated_at', 'is_active', 'owner',
            'member_count', 'is_owner', 'current_user_role',
            'is_sponsor', 'can_start_subscription'
        )
        read_only_fields = ('owner', 'created_at', 'updated_at')

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner == request.user
        return False

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                membership = OrganizationMembership.objects.get(
                    organization=obj,
                    user=request.user
                )
                return membership.role
            except OrganizationMembership.DoesNotExist:
                return None
        return None

    def get_is_sponsor(self, obj):
        user = self.context.get('request').user
        return obj.sponsor == user

    def get_can_start_subscription(self, obj):
        user = self.context.get('request').user
        return obj.sponsor == user and obj.plan != 'pro'

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = (
            'id', 'organization', 'organization_name', 'user', 'user_email',
            'user_full_name', 'role', 'can_manage_members', 'can_manage_settings',
            'can_manage_billing', 'can_view_reports', 'can_create_transactions',
            'can_approve_transactions', 'joined_at', 'invited_by',
            'invitation_accepted_at', 'last_active_at'
        )
        read_only_fields = (
            'organization', 'user', 'joined_at', 'invited_by',
            'invitation_accepted_at', 'last_active_at'
        )

class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)

    class Meta:
        model = OrganizationInvitation
        fields = (
            'id', 'organization', 'organization_name', 'email', 'invited_by',
            'invited_by_name', 'role', 'status', 'message', 'created_at',
            'expires_at', 'accepted_at', 'accepted_by'
        )
        read_only_fields = (
            'status', 'token', 'created_at', 'expires_at',
            'accepted_at', 'accepted_by'
        )

    def validate(self, data):
        # Check if user is already a member
        try:
            OrganizationMembership.objects.get(
                organization=data['organization'],
                user__email=data['email']
            )
            raise serializers.ValidationError(
                _("User is already a member of this organization")
            )
        except OrganizationMembership.DoesNotExist:
            pass

        # Check for pending invitations
        pending_invitation = OrganizationInvitation.objects.filter(
            organization=data['organization'],
            email=data['email'],
            status=OrganizationInvitation.StatusChoices.PENDING
        ).first()
        
        if pending_invitation:
            raise serializers.ValidationError(
                _("There is already a pending invitation for this email")
            )

        return data

    def create(self, validated_data):
        if 'expires_at' not in validated_data or not validated_data['expires_at']:
            validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        return super().create(validated_data)

class IncentiveSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    class Meta:
        model = Incentive
        fields = ['id', 'type', 'status', 'created_at', 'granted_at', 'organization', 'organization_name']
        read_only_fields = ['id', 'created_at', 'granted_at', 'organization_name'] 