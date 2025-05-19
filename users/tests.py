from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Role, User

class RoleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        # Create a test permission
        content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type,
        )

    def test_create_role(self):
        """Test creating a role with permissions"""
        role = Role.objects.create(
            name='Test Role',
            description='Test Description'
        )
        role.permissions.add(self.permission)
        
        self.assertEqual(role.name, 'test_role')  # name should be lowercase
        self.assertEqual(role.description, 'Test Description')
        self.assertEqual(role.permissions.count(), 1)
        self.assertFalse(role.is_system_role)

    def test_role_str_representation(self):
        """Test the string representation of Role"""
        role = Role.objects.create(name='Test Role')
        self.assertEqual(str(role), 'test_role')

class RoleAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
        # Create test permission
        content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type,
        )
        # Create test roles
        self.system_role = Role.objects.create(
            name='System Role',
            is_system_role=True
        )
        self.regular_role = Role.objects.create(
            name='Regular Role'
        )

    def test_list_roles_superuser(self):
        """Test that superuser can list all roles"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(reverse('users:role-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should see both roles

    def test_list_roles_staff(self):
        """Test that staff can only list non-system roles"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(reverse('users:role-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see regular role

    def test_list_roles_regular_user(self):
        """Test that regular user can only see assigned roles"""
        self.client.force_authenticate(user=self.regular_user)
        self.regular_user.roles.add(self.regular_role)
        response = self.client.get(reverse('users:role-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see assigned role

    def test_create_role_superuser(self):
        """Test that superuser can create roles"""
        self.client.force_authenticate(user=self.superuser)
        data = {
            'name': 'New Role',
            'description': 'New Description',
            'permission_ids': [self.permission.id]
        }
        response = self.client.post(reverse('users:role-list'), data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.count(), 3)
        self.assertEqual(
            Role.objects.get(name='new_role').permissions.count(),
            1
        )

    def test_create_role_staff(self):
        """Test that staff can create non-system roles"""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'name': 'New Role',
            'description': 'New Description'
        }
        response = self.client.post(reverse('users:role-list'), data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_system_role'])

    def test_create_role_regular_user(self):
        """Test that regular user cannot create roles"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'New Role',
            'description': 'New Description'
        }
        response = self.client.post(reverse('users:role-list'), data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_system_role(self):
        """Test that only superuser can update system roles"""
        url = reverse('users:role-detail', args=[self.system_role.id])
        data = {'name': 'Updated System Role'}

        # Test with superuser
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test with staff user
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_role(self):
        """Test role deletion restrictions"""
        # Try to delete system role
        url = reverse('users:role-detail', args=[self.system_role.id])
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Delete regular role
        url = reverse('users:role-detail', args=[self.regular_role.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_permissions_to_role(self):
        """Test adding permissions to a role"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('users:role-add-permissions', args=[self.regular_role.id])
        data = {'permission_ids': [self.permission.id]}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.regular_role.permissions.count(), 1)

    def test_remove_permissions_from_role(self):
        """Test removing permissions from a role"""
        self.regular_role.permissions.add(self.permission)
        self.client.force_authenticate(user=self.superuser)
        url = reverse('users:role-remove-permissions', args=[self.regular_role.id])
        data = {'permission_ids': [self.permission.id]}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.regular_role.permissions.count(), 0)

    def test_available_permissions(self):
        """Test listing available permissions based on user type"""
        url = reverse('users:role-available-permissions')

        # Test superuser sees all permissions
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_perms_count = len(response.data)

        # Test staff user sees filtered permissions
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) < all_perms_count)

        # Test regular user sees only their permissions
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No permissions assigned yet
