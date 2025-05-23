from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMembership
import json
import stripe
from django.conf import settings
from unittest.mock import patch, MagicMock

User = get_user_model()

class StripeIntegrationTests(TestCase):
    def setUp(self):
        # Configurar Stripe en modo test
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Crear usuarios de prueba
        self.owner = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        self.sponsor = User.objects.create_user(
            email='sponsor@test.com',
            password='testpass123',
            first_name='Sponsor',
            last_name='Test'
        )
        
        # Crear organización de prueba
        self.organization = Organization.objects.create(
            name='Test Org',
            slug='test-org',
            owner=self.owner,
            sponsor=self.sponsor,
            sponsor_type='accountant'
        )
        
        # Crear membresías
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role='owner'
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.sponsor,
            role='accountant'
        )
        
        # Configurar cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.sponsor)

    @patch('stripe.Customer.create')
    def test_create_stripe_customer(self, mock_create):
        mock_create.return_value = MagicMock(id='cus_test123')
        
        # Intentar iniciar suscripción
        url = reverse('organizations:organization-start-subscription', args=[self.organization.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('checkout_url', response.data)
        mock_create.assert_called_once()

    def test_only_sponsor_can_start_subscription(self):
        # Intentar iniciar suscripción como owner (no sponsor)
        self.client.force_authenticate(user=self.owner)
        url = reverse('organizations:organization-start-subscription', args=[self.organization.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_subscription_created(self, mock_construct):
        # Simular evento de suscripción creada
        mock_construct.return_value = {
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'metadata': {'org_id': str(self.organization.id)},
                    'status': 'active'
                }
            }
        }
        
        # Simular webhook
        url = reverse('organizations:stripe-webhook')
        response = self.client.post(
            url,
            data=json.dumps({'type': 'customer.subscription.created'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.plan, 'pro')

    def test_transfer_sponsorship(self):
        # Transferir sponsorship al owner
        self.client.force_authenticate(user=self.owner)
        url = reverse('organizations:organization-transfer-sponsorship', args=[self.organization.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.sponsor, self.owner)
        self.assertEqual(self.organization.sponsor_type, 'client')

    def test_organization_serializer_sponsor_fields(self):
        # Verificar campos de sponsor en el serializer
        url = reverse('organizations:organization-detail', args=[self.organization.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_sponsor'])
        self.assertTrue(response.data['can_start_subscription']) 