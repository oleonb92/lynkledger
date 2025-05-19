from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from .models import Organization, OrganizationMembership, OrganizationInvitation

User = get_user_model()

class OrganizationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )

    def test_organization_creation(self):
        self.assertEqual(self.organization.name, 'Test Organization')
        self.assertEqual(self.organization.owner, self.user)
        self.assertTrue(self.organization.is_active)

    def test_member_management(self):
        new_user = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='member123'
        )
        
        # Test adding member
        membership = self.organization.add_member(new_user, 'member')
        self.assertEqual(membership.role, 'member')
        self.assertEqual(self.organization.get_member_count(), 1)

        # Test removing member
        self.organization.remove_member(new_user)
        self.assertEqual(self.organization.get_member_count(), 0)

class OrganizationMembershipModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='owner123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='member123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role='manager'
        )

    def test_membership_creation(self):
        self.assertEqual(self.membership.organization, self.organization)
        self.assertEqual(self.membership.user, self.member)
        self.assertEqual(self.membership.role, 'manager')

    def test_permission_management(self):
        permissions = {
            'can_manage_members': True,
            'can_manage_settings': True,
            'can_view_reports': True
        }
        self.membership.update_permissions(permissions)
        
        self.assertTrue(self.membership.can_manage_members)
        self.assertTrue(self.membership.can_manage_settings)
        self.assertTrue(self.membership.can_view_reports)

class OrganizationInvitationModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='owner123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )

    def test_invitation_creation(self):
        invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            email='invite@example.com',
            invited_by=self.owner,
            role='member',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        self.assertTrue(invitation.token)
        self.assertEqual(invitation.status, 'pending')
        self.assertTrue(invitation.is_valid())

    def test_invitation_acceptance(self):
        invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            email='invite@example.com',
            invited_by=self.owner,
            role='member',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        new_user = User.objects.create_user(
            username='newmember',
            email='invite@example.com',
            password='member123'
        )
        
        membership = invitation.accept(new_user)
        self.assertIsNotNone(membership)
        self.assertEqual(invitation.status, 'accepted')
        self.assertEqual(membership.role, 'member')

class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.user
        )

    def test_create_organization(self):
        data = {
            'name': 'New Organization',
            'slug': 'new-org',
            'organization_type': 'business'
        }
        response = self.client.post('/api/organizations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 2)

    def test_invite_member(self):
        data = {
            'email': 'invite@example.com',
            'role': 'member',
            'message': 'Please join our organization'
        }
        response = self.client.post(
            f'/api/organizations/{self.organization.id}/invite/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationInvitation.objects.count(), 1)

    def test_list_members(self):
        response = self.client.get(
            f'/api/organizations/{self.organization.id}/members/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class OrganizationMembershipAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='owner123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='member123'
        )
        self.client.force_authenticate(user=self.owner)
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role='member'
        )

    def test_update_member_role(self):
        data = {
            'role': 'manager',
            'can_manage_members': True
        }
        response = self.client.patch(
            f'/api/organization-memberships/{self.membership.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.role, 'manager')

    def test_remove_member(self):
        response = self.client.delete(
            f'/api/organization-memberships/{self.membership.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrganizationMembership.objects.count(), 0)

class OrganizationInvitationAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='owner123'
        )
        self.client.force_authenticate(user=self.owner)
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            owner=self.owner
        )
        self.invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            email='invite@example.com',
            invited_by=self.owner,
            role='member',
            expires_at=timezone.now() + timedelta(days=7)
        )

    def test_accept_invitation(self):
        new_user = User.objects.create_user(
            username='newmember',
            email='invite@example.com',
            password='member123'
        )
        self.client.force_authenticate(user=new_user)
        
        response = self.client.post(
            f'/api/organization-invitations/{self.invitation.id}/accept/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, 'accepted')

    def test_reject_invitation(self):
        new_user = User.objects.create_user(
            username='newmember',
            email='invite@example.com',
            password='member123'
        )
        self.client.force_authenticate(user=new_user)
        
        response = self.client.post(
            f'/api/organization-invitations/{self.invitation.id}/reject/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, 'rejected')
