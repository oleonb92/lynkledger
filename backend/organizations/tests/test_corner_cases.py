from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership, Incentive
from unittest.mock import patch
from django.db.models.deletion import ProtectedError
import json

User = get_user_model()

@override_settings(
    STRIPE_SECRET_KEY='sk_test_mock',
    STRIPE_WEBHOOK_SECRET='whsec_mock',
    STRIPE_PLAN_ID='price_mock',
    FRONTEND_URL='http://localhost:3000'
)
class CornerCaseTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        self.accountant = User.objects.create_user(
            username='accountant',
            email='accountant@test.com',
            password='testpass123',
            first_name='Accountant',
            last_name='Test'
        )
        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org',
            owner=self.owner,
            sponsor=self.accountant,
            sponsor_type='accountant',
            plan='pro'
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.owner,
            role='owner'
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.accountant,
            role='accountant',
            pro_features_for_accountant=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.accountant)

    @patch('stripe.Webhook.construct_event')
    def test_downgrade_to_free(self, mock_construct_event):
        # Simula evento de downgrade
        from organizations import stripe_webhook
        event = {
            'type': 'customer.subscription.updated',
            'data': {'object': {'metadata': {'org_id': str(self.org.id)}, 'status': 'canceled'}}
        }
        mock_construct_event.return_value = event
        request = self.client.post(
            reverse('organizations:stripe-webhook'),
            data=json.dumps({}),  # El payload real no importa porque lo mockeamos
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, 'free')
        membership = OrganizationMembership.objects.get(organization=self.org, user=self.accountant)
        self.assertTrue(membership.pro_features_for_accountant)

    @patch('stripe.Webhook.construct_event')
    def test_upgrade_and_no_duplicate_incentive(self, mock_construct_event):
        from organizations import stripe_webhook
        event = {
            'type': 'customer.subscription.created',
            'data': {'object': {'metadata': {'org_id': str(self.org.id)}}}
        }
        mock_construct_event.return_value = event
        # Primer upgrade
        self.client.post(
            reverse('organizations:stripe-webhook'),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        # Segundo upgrade (no debe duplicar)
        self.client.post(
            reverse('organizations:stripe-webhook'),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        incentives = Incentive.objects.filter(user=self.accountant, organization=self.org)
        self.assertEqual(incentives.count(), 1)

    def test_delete_sponsor(self):
        self.accountant.delete()
        self.org.refresh_from_db()
        self.assertIsNone(self.org.sponsor)
        self.assertTrue(User.objects.filter(id=self.owner.id).exists())

    def test_delete_owner(self):
        # Espera que lanzar ProtectedError al intentar borrar el owner
        with self.assertRaises(ProtectedError):
            self.owner.delete()
        self.org.refresh_from_db()
        self.assertEqual(self.org.owner, self.owner) 