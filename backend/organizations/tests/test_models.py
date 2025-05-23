from django.test import TestCase
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
from django.core.exceptions import ValidationError

User = get_user_model()

class OrganizationModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        self.sponsor = User.objects.create_user(
            username='sponsor',
            email='sponsor@test.com',
            password='testpass123',
            first_name='Sponsor',
            last_name='Test'
        )
        self.organization = Organization.objects.create(
            name='Test Org',
            slug='test-org',
            owner=self.owner,
            sponsor=self.sponsor,
            sponsor_type='accountant'
        )

    def test_organization_creation(self):
        self.assertEqual(self.organization.plan, 'free')
        self.assertEqual(self.organization.sponsor, self.sponsor)
        self.assertEqual(self.organization.sponsor_type, 'accountant')

    def test_transfer_sponsorship(self):
        # Transferir sponsorship al owner
        self.organization.transfer_sponsorship(self.owner, 'client')
        self.organization.refresh_from_db()
        
        self.assertEqual(self.organization.sponsor, self.owner)
        self.assertEqual(self.organization.sponsor_type, 'client')

    def test_organization_membership_creation(self):
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role='owner'
        )
        
        self.assertEqual(membership.role, 'owner')
        self.assertFalse(membership.pro_features_for_accountant)

    def test_organization_membership_pro_features(self):
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.sponsor,
            role='accountant',
            pro_features_for_accountant=True
        )
        
        self.assertTrue(membership.pro_features_for_accountant)
        
        # Actualizar plan de la organización
        self.organization.plan = 'pro'
        self.organization.save()
        
        # Verificar que el contador mantiene sus features pro
        membership.refresh_from_db()
        self.assertTrue(membership.pro_features_for_accountant)

    def test_organization_membership_permissions(self):
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.sponsor,
            role='accountant'
        )
        
        # Verificar permisos por defecto
        self.assertFalse(membership.can_manage_members)
        self.assertFalse(membership.can_manage_settings)
        self.assertFalse(membership.can_manage_billing)
        self.assertTrue(membership.can_view_reports)
        self.assertFalse(membership.can_create_transactions)
        self.assertFalse(membership.can_approve_transactions)
        
        # Actualizar permisos
        membership.update_permissions({
            'can_manage_members': True,
            'can_manage_billing': True
        })
        
        membership.refresh_from_db()
        self.assertTrue(membership.can_manage_members)
        self.assertTrue(membership.can_manage_billing) 