from django.shortcuts import render
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Role
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    RoleSerializer,
    PermissionSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        if not user.check_password(serializer.data.get('old_password')):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.data.get('new_password'))
        user.save()
        return Response(
            {'message': 'Password updated successfully'},
            status=status.HTTP_200_OK
        )

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter roles based on user permissions:
        - Superusers can see all roles
        - Staff users can see non-system roles
        - Regular users can only see their assigned roles
        """
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.is_staff:
            return self.queryset.filter(is_system_role=False)
        return user.roles.all()

    def perform_create(self, serializer):
        """Create a new role"""
        # Only staff and superusers can create roles
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                _("You don't have permission to create roles.")
            )
        serializer.save()

    def perform_update(self, serializer):
        """Update a role"""
        instance = self.get_object()
        # Prevent modification of system roles by non-superusers
        if instance.is_system_role and not self.request.user.is_superuser:
            raise permissions.PermissionDenied(
                _("You don't have permission to modify system roles.")
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Delete a role"""
        # Prevent deletion of system roles
        if instance.is_system_role:
            raise permissions.PermissionDenied(
                _("System roles cannot be deleted.")
            )
        instance.delete()

    @action(detail=False, methods=['get'])
    def available_permissions(self, request):
        """
        Get list of all available permissions that can be assigned to roles.
        Filters out permissions based on user's access level.
        """
        user = request.user
        if user.is_superuser:
            permissions = Permission.objects.all()
        elif user.is_staff:
            # Staff can see all permissions except sensitive ones
            permissions = Permission.objects.exclude(
                Q(content_type__app_label__in=['auth', 'admin']) |
                Q(content_type__model__in=['user', 'group', 'permission'])
            )
        else:
            # Regular users can only see their current permissions
            permissions = user.user_permissions.all()

        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_permissions(self, request, pk=None):
        """Add permissions to a role"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        # Validate permissions
        try:
            permissions = Permission.objects.filter(id__in=permission_ids)
            if len(permissions) != len(permission_ids):
                return Response(
                    {'error': _('Some permission IDs are invalid.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': _('Invalid permission IDs format.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add permissions
        role.permissions.add(*permissions)
        serializer = self.get_serializer(role)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_permissions(self, request, pk=None):
        """Remove permissions from a role"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        # Validate permissions
        try:
            permissions = Permission.objects.filter(id__in=permission_ids)
        except ValueError:
            return Response(
                {'error': _('Invalid permission IDs format.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove permissions
        role.permissions.remove(*permissions)
        serializer = self.get_serializer(role)
        return Response(serializer.data)
