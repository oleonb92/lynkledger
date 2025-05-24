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
from .models import Organization, OrganizationMembership, OrganizationInvitation, Incentive
from .serializers import (
    OrganizationSerializer,
    OrganizationMembershipSerializer,
    OrganizationInvitationSerializer,
    IncentiveSerializer
)
from django.core.mail import send_mail
import os
from rest_framework.permissions import AllowAny, IsAuthenticated
from .stripe_utils import create_stripe_customer
import stripe
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar organizaciones.
    
    Permite crear, listar, actualizar y eliminar organizaciones.
    También proporciona endpoints adicionales para gestionar membresías,
    invitaciones y suscripciones.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            Q(owner=self.request.user) |
            Q(members=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @swagger_auto_schema(
        operation_description="Lista los miembros de una organización",
        responses={
            200: OrganizationMembershipSerializer(many=True),
            404: "Organización no encontrada"
        }
    )
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        organization = self.get_object()
        memberships = OrganizationMembership.objects.filter(organization=organization)
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Transfiere la propiedad de la organización a otro miembro",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['new_owner_id'],
            properties={
                'new_owner_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del nuevo propietario')
            }
        ),
        responses={
            200: "Propiedad transferida exitosamente",
            403: "No tienes permiso para transferir la propiedad",
            404: "Usuario no encontrado"
        }
    )
    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        organization = self.get_object()
        
        if organization.owner != request.user:
            return Response(
                {'detail': _("Only the owner can transfer ownership")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_owner_id = request.data.get('new_owner_id')
        try:
            new_owner = organization.members.get(id=new_owner_id)
        except User.DoesNotExist:
            return Response(
                {'detail': _("User must be a member of the organization")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_owner = organization.owner
        organization.owner = new_owner
        organization.save()
        
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

    @swagger_auto_schema(
        operation_description="Inicia el proceso de suscripción para una organización",
        responses={
            200: openapi.Response(
                description="URL de checkout generada exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'checkout_url': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            403: "No tienes permiso para iniciar la suscripción"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start_subscription(self, request, pk=None):
        org = self.get_object()
        user = request.user
        if org.sponsor != user:
            return Response({'detail': 'Solo el sponsor puede iniciar la suscripción.'}, status=403)
        
        customer_id = create_stripe_customer(user)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': settings.STRIPE_PLAN_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=settings.FRONTEND_URL + '/billing/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.FRONTEND_URL + '/billing/cancel',
            metadata={'org_id': org.id},
        )
        return Response({'checkout_url': session.url})

    @swagger_auto_schema(
        operation_description="Transfiere el patrocinio de la organización a otro usuario",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['new_sponsor_id'],
            properties={
                'new_sponsor_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del nuevo sponsor'),
                'sponsor_type': openapi.Schema(type=openapi.TYPE_STRING, description='Tipo de sponsor (accountant/client)')
            }
        ),
        responses={
            200: "Patrocinio transferido exitosamente",
            403: "No tienes permiso para transferir el patrocinio",
            404: "Usuario no encontrado"
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def transfer_sponsorship(self, request, pk=None):
        org = self.get_object()
        user = request.user
        new_sponsor_id = request.data.get('new_sponsor_id')
        sponsor_type = request.data.get('sponsor_type', 'client')
        
        if org.owner != user:
            return Response({'detail': 'Solo el owner puede transferir el sponsorship.'}, status=403)
        
        if not new_sponsor_id:
            return Response({'detail': 'Debes especificar el nuevo sponsor.'}, status=400)
        
        try:
            new_sponsor = org.members.get(id=new_sponsor_id)
        except Exception:
            return Response({'detail': 'El nuevo sponsor debe ser miembro de la organización.'}, status=400)
        
        org.transfer_sponsorship(new_sponsor=new_sponsor, sponsor_type=sponsor_type)
        return Response({
            'detail': 'Sponsorship transferido correctamente.',
            'new_sponsor': new_sponsor.email,
            'sponsor_type': sponsor_type
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_sponsor(self, request, pk=None):
        org = self.get_object()
        user = request.user
        if org.sponsor != user and org.owner != user:
            return Response({'detail': 'Solo el sponsor o el owner pueden remover el sponsor.'}, status=403)
        # Si el sponsor es removido, el owner (cliente) debe asumir el pago
        org.sponsor = org.owner
        org.sponsor_type = 'client'
        org.save()
        # (Opcional) Aquí puedes notificar al owner que ahora es el sponsor
        return Response({'detail': 'El sponsor ha sido removido. El owner ahora es el sponsor y debe asumir el pago.'})

    @action(detail=False, methods=['get'], url_path='accountant_panel')
    def accountant_panel(self, request):
        # Organizaciones donde el usuario es accountant
        accountant_memberships = OrganizationMembership.objects.filter(
            user=request.user,
            role=OrganizationMembership.RoleChoices.ACCOUNTANT
        ).select_related('organization')
        data = []
        for membership in accountant_memberships:
            org = membership.organization
            incentives = org.incentives.filter(user=request.user)
            data.append({
                'organization': OrganizationSerializer(org, context={'request': request}).data,
                'plan': org.plan,
                'pro_features_for_accountant': membership.pro_features_for_accountant,
                'incentives': IncentiveSerializer(incentives, many=True).data
            })
        return Response(data)

    @action(detail=True, methods=['get'], url_path='pro_status')
    def pro_status(self, request, pk=None):
        org = self.get_object()
        # Busca si el usuario es accountant en esta organización
        try:
            membership = OrganizationMembership.objects.get(
                organization=org,
                user=request.user,
                role=OrganizationMembership.RoleChoices.ACCOUNTANT
            )
            pro_access = membership.pro_features_for_accountant
        except OrganizationMembership.DoesNotExist:
            pro_access = False
        return Response({
            'organization': OrganizationSerializer(org, context={'request': request}).data,
            'plan': org.plan,
            'accountant_has_pro': pro_access
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_incentives(self, request):
        """Endpoint para que el contador vea sus incentivos."""
        user = request.user
        incentives = Incentive.objects.filter(user=user, status__in=['pending', 'granted'])
        serializer = IncentiveSerializer(incentives, many=True)
        return Response(serializer.data)

class OrganizationMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar membresías de organizaciones.
    
    Permite crear, listar, actualizar y eliminar membresías.
    También proporciona endpoints para gestionar roles y permisos.
    """
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
    """
    API endpoint para gestionar invitaciones a organizaciones.
    
    Permite crear, listar, actualizar y eliminar invitaciones.
    También proporciona endpoints para aceptar y rechazar invitaciones.
    """
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'token'

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
        context = {
            'organization': organization,
            'role': invitation.role,
            'invite_link': invite_link,
            'expires_at': invitation.expires_at.strftime('%Y-%m-%d %H:%M'),
            'year': timezone.now().year,
        }
        html_message = render_to_string('organizations/email/invitation.html', context)
        plain_message = strip_tags(html_message)
        send_mail(
            subject=f"Invitación a unirse a {organization.name} en LynkLedger",
            message=plain_message,
            from_email=None,
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def resend(self, request, token=None):
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
        context = {
            'organization': invitation.organization,
            'role': invitation.role,
            'invite_link': invite_link,
            'expires_at': invitation.expires_at.strftime('%Y-%m-%d %H:%M'),
            'year': timezone.now().year,
        }
        html_message = render_to_string('organizations/email/invitation.html', context)
        plain_message = strip_tags(html_message)
        send_mail(
            subject=f"Invitación a unirse a {invitation.organization.name} en LynkLedger",
            message=plain_message,
            from_email=None,
            recipient_list=[invitation.email],
            html_message=html_message,
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

class IncentiveViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar incentivos.
    
    Permite crear, listar, actualizar y eliminar incentivos.
    También proporciona endpoints para reclamar y usar incentivos.
    """
    serializer_class = IncentiveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Incentive.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        incentive = self.get_object()
        if incentive.status != 'pending':
            return Response({'detail': 'El incentivo no está pendiente.'}, status=400)
        incentive.status = 'granted'
        incentive.granted_at = timezone.now()
        incentive.save()
        # (Opcional) Notificar por email
        return Response({'detail': 'Incentivo reclamado correctamente.'})

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        incentive = self.get_object()
        if incentive.status != 'granted':
            return Response({'detail': 'El incentivo debe estar otorgado para poder usarse.'}, status=400)
        incentive.status = 'used'
        incentive.save()
        return Response({'detail': 'Incentivo marcado como usado.'})

    @action(detail=False, methods=['get'])
    def history(self, request):
        incentives = Incentive.objects.filter(user=request.user)
        serializer = self.get_serializer(incentives, many=True)
        return Response(serializer.data)
