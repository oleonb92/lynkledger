from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import HttpResponse
import csv
import json
from datetime import datetime
from .models import Organization, OrganizationMembership, OrganizationInvitation
from .serializers import (
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    OrganizationInvitationSerializer
)
from django.core.mail import send_mail
import os
from rest_framework.permissions import AllowAny

# Create your views here.

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            Q(owner=self.request.user) |
            Q(members=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        organization = self.get_object()
        memberships = OrganizationMembership.objects.filter(organization=organization)
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        organization = self.get_object()
        
        # Verify current user is the owner
        if organization.owner != request.user:
            return Response(
                {'detail': _("Only the owner can transfer ownership")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the new owner
        new_owner_id = request.data.get('new_owner_id')
        try:
            new_owner = organization.members.get(id=new_owner_id)
        except User.DoesNotExist:
            return Response(
                {'detail': _("User must be a member of the organization")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update ownership
        old_owner = organization.owner
        organization.owner = new_owner
        organization.save()
        
        # Update memberships
        OrganizationMembership.objects.filter(
            organization=organization,
            user=new_owner
        ).update(role='owner')
        
        OrganizationMembership.objects.filter(
            organization=organization,
            user=old_owner
        ).update(role='admin')
        
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def update_billing(self, request, pk=None):
        organization = self.get_object()
        
        # Check permissions
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user=request.user
        )
        if not (membership.role in ['owner', 'admin'] or membership.can_manage_billing):
            return Response(
                {'detail': _("You don't have permission to manage billing")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update billing information
        billing_data = request.data.get('billing_info', {})
        # TODO: Integrate with payment processor
        
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def export_data(self, request, pk=None):
        organization = self.get_object()
        
        # Check permissions
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user=request.user
        )
        if not (membership.role in ['owner', 'admin']):
            return Response(
                {'detail': _("Only owners and admins can export data")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prepare data for export
        data = {
            'organization': {
                'name': organization.name,
                'type': organization.organization_type,
                'created_at': organization.created_at.isoformat(),
            },
            'members': [],
            'invitations': []
        }
        
        # Add member data
        for membership in organization.memberships.all():
            data['members'].append({
                'email': membership.user.email,
                'role': membership.role,
                'joined_at': membership.joined_at.isoformat()
            })
        
        # Add invitation data
        for invitation in organization.invitations.all():
            data['invitations'].append({
                'email': invitation.email,
                'status': invitation.status,
                'created_at': invitation.created_at.isoformat()
            })
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"organization_export_{organization.slug}_{timestamp}.json"
        
        # Create the response
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

    @action(detail=True, methods=['post'])
    def create_team(self, request, pk=None):
        organization = self.get_object()
        
        # Check permissions
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user=request.user
        )
        if not (membership.role in ['owner', 'admin'] or membership.can_manage_members):
            return Response(
                {'detail': _("You don't have permission to create teams")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create team
        team_data = request.data
        # TODO: Implement team creation logic
        
        return Response(status=status.HTTP_201_CREATED)

class OrganizationMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrganizationMembership.objects.filter(
            Q(organization__owner=self.request.user) |
            Q(organization__memberships__user=self.request.user, 
              organization__memberships__can_manage_members=True)
        ).distinct()

    def perform_update(self, serializer):
        membership = self.get_object()
        if membership.role == 'owner':
            raise serializers.ValidationError(
                _("Cannot modify the owner's membership")
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.role == 'owner':
            raise serializers.ValidationError(
                _("Cannot remove the owner from the organization")
            )
        instance.delete()

class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, 'action', None) == 'retrieve':
            return OrganizationInvitation.objects.all()
        return OrganizationInvitation.objects.filter(
            Q(organization__owner=self.request.user) |
            Q(organization__memberships__user=self.request.user,
              organization__memberships__can_manage_members=True) |
            Q(email=self.request.user.email)
        ).distinct()

    def create(self, request, *args, **kwargs):
        # Validar permisos
        organization_id = request.data.get('organization')
        organization = get_object_or_404(Organization, id=organization_id)
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user=request.user
        )
        if not (membership.role in ['owner', 'admin'] or membership.can_manage_members):
            return Response(
                {'detail': _("You don't have permission to invite members")},
                status=status.HTTP_403_FORBIDDEN
            )

        # Crear invitación
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save(invited_by=request.user)

        # Enviar email de invitación
        FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        invite_link = f"{FRONTEND_URL}/accept-invite/{invitation.token}"
        send_mail(
            subject=f"Invitación a unirse a {organization.name} en LynkLedger",
            message=f"Hola! Has sido invitado a unirte a la organización '{organization.name}' como {invitation.role}.\n\nHaz click en el siguiente enlace para aceptar la invitación:\n{invite_link}\n\nEste enlace expirará el {invitation.expires_at.strftime('%Y-%m-%d %H:%M')}.",
            from_email=None,
            recipient_list=[invitation.email],
            fail_silently=False,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        invitation = self.get_object()
        if invitation.status != OrganizationInvitation.StatusChoices.PENDING:
            return Response({'detail': _('Only pending invitations can be resent')}, status=status.HTTP_400_BAD_REQUEST)

        # Permisos: solo owner, admin o quien puede gestionar miembros
        membership = OrganizationMembership.objects.filter(
            organization=invitation.organization,
            user=request.user
        ).first()
        if not (membership and (membership.role in ['owner', 'admin'] or membership.can_manage_members)):
            return Response({'detail': _("You don't have permission to resend invitations")}, status=status.HTTP_403_FORBIDDEN)

        # Reenviar email
        FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        invite_link = f"{FRONTEND_URL}/accept-invite/{invitation.token}"
        send_mail(
            subject=f"Invitación a unirse a {invitation.organization.name} en LynkLedger",
            message=f"Hola! Has sido invitado a unirte a la organización '{invitation.organization.name}' como {invitation.role}.\n\nHaz click en el siguiente enlace para aceptar la invitación:\n{invite_link}\n\nEste enlace expirará el {invitation.expires_at.strftime('%Y-%m-%d %H:%M')}.",
            from_email=None,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
        return Response({'detail': _('Invitation resent successfully')}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        invitation = self.get_object()
        
        if invitation.email != request.user.email:
            return Response(
                {'detail': _("This invitation is not for you")},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if not invitation.is_valid():
            return Response(
                {'detail': _("This invitation is no longer valid")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        membership = invitation.accept(request.user)
        if membership:
            return Response(
                OrganizationMembershipSerializer(membership).data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': _("Could not accept invitation")},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        invitation = self.get_object()
        
        if invitation.email != request.user.email:
            return Response(
                {'detail': _("This invitation is not for you")},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if invitation.reject():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': _("Could not reject invitation")},
            status=status.HTTP_400_BAD_REQUEST
        )
