from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Organization, OrganizationMembership, OrganizationInvitation
from .serializers import (
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    OrganizationInvitationSerializer
)

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
    def invite(self, request, pk=None):
        organization = self.get_object()
        
        # Check if user has permission to invite
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

        serializer = OrganizationInvitationSerializer(data={
            **request.data,
            'organization': organization.id,
            'invited_by': request.user.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # TODO: Send invitation email
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    def get_queryset(self):
        return OrganizationInvitation.objects.filter(
            Q(organization__owner=self.request.user) |
            Q(organization__memberships__user=self.request.user,
              organization__memberships__can_manage_members=True) |
            Q(email=self.request.user.email)
        ).distinct()

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
