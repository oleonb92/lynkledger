from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from organizations.models import Organization
from .models import (
    Account, Transaction, Budget, Invoice,
    FixedAsset, TaxRate, Payment, RecurringInvoice
)

User = get_user_model()

class AccountingAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

    def test_create_account(self):
        data = {
            'name': 'Cash',
            'code': '1000',
            'account_type': 'asset',
            'subtype': 'cash'
        }
        response = self.client.post('/api/accounting/accounts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Account.objects.get().name, 'Cash')

    def test_create_transaction(self):
        # Create accounts first
        cash = Account.objects.create(
            organization=self.organization,
            name='Cash',
            code='1000',
            account_type='asset',
            subtype='cash'
        )
        revenue = Account.objects.create(
            organization=self.organization,
            name='Revenue',
            code='4000',
            account_type='income',
            subtype='sales'
        )

        data = {
            'date': '2024-01-01',
            'description': 'Test transaction',
            'entries': [
                {
                    'account': cash.id,
                    'amount': 1000.00
                },
                {
                    'account': revenue.id,
                    'amount': -1000.00
                }
            ]
        }
        response = self.client.post('/api/accounting/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_create_invoice(self):
        # Create necessary accounts
        receivable = Account.objects.create(
            organization=self.organization,
            name='Accounts Receivable',
            code='1100',
            account_type='asset',
            subtype='receivable'
        )
        revenue = Account.objects.create(
            organization=self.organization,
            name='Revenue',
            code='4000',
            account_type='income',
            subtype='sales'
        )

        data = {
            'date': '2024-01-01',
            'due_date': '2024-01-31',
            'party_name': 'Test Customer',
            'items': [
                {
                    'description': 'Test Item',
                    'quantity': 1,
                    'unit_price': 100.00,
                    'income_account': revenue.id
                }
            ]
        }
        response = self.client.post('/api/accounting/invoices/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_create_budget(self):
        # Create account
        expense = Account.objects.create(
            organization=self.organization,
            name='Office Expenses',
            code='5000',
            account_type='expense',
            subtype='operating'
        )

        data = {
            'name': 'Q1 2024 Budget',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31',
            'period': 'monthly',
            'items': [
                {
                    'account': expense.id,
                    'amount': 1000.00
                }
            ]
        }
        response = self.client.post('/api/accounting/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Budget.objects.count(), 1)

    def test_create_fixed_asset(self):
        data = {
            'name': 'Office Equipment',
            'asset_number': 'FA001',
            'purchase_date': '2024-01-01',
            'purchase_cost': 5000.00,
            'useful_life_years': 5,
            'depreciation_method': 'straight_line',
            'current_value': 5000.00
        }
        response = self.client.post('/api/accounting/fixed-assets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FixedAsset.objects.count(), 1)

    def test_create_tax_rate(self):
        # Create tax accounts
        sales_tax = Account.objects.create(
            organization=self.organization,
            name='Sales Tax Payable',
            code='2200',
            account_type='liability',
            subtype='payable'
        )
        purchase_tax = Account.objects.create(
            organization=self.organization,
            name='Purchase Tax Receivable',
            code='1200',
            account_type='asset',
            subtype='receivable'
        )

        data = {
            'name': 'VAT 20%',
            'rate': 20.00,
            'sales_tax_account': sales_tax.id,
            'purchase_tax_account': purchase_tax.id
        }
        response = self.client.post('/api/accounting/tax-rates/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaxRate.objects.count(), 1)

    def test_create_payment(self):
        # Create necessary accounts and invoice
        bank = Account.objects.create(
            organization=self.organization,
            name='Bank Account',
            code='1010',
            account_type='asset',
            subtype='bank'
        )
        invoice = Invoice.objects.create(
            organization=self.organization,
            number='INV001',
            date='2024-01-01',
            due_date='2024-01-31',
            party_name='Test Customer',
            total=1000.00
        )

        data = {
            'invoice': invoice.id,
            'date': '2024-01-15',
            'amount': 1000.00,
            'method': 'bank_transfer',
            'bank_account': bank.id
        }
        response = self.client.post('/api/accounting/payments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

    def test_create_recurring_invoice(self):
        # Create income account
        revenue = Account.objects.create(
            organization=self.organization,
            name='Revenue',
            code='4000',
            account_type='income',
            subtype='sales'
        )

        data = {
            'name': 'Monthly Service',
            'start_date': '2024-01-01',
            'frequency': 'monthly',
            'next_date': '2024-01-01',
            'party_name': 'Test Customer',
            'items': [
                {
                    'description': 'Monthly Service Fee',
                    'quantity': 1,
                    'unit_price': 100.00,
                    'income_account': revenue.id
                }
            ]
        }
        response = self.client.post('/api/accounting/recurring-invoices/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecurringInvoice.objects.count(), 1)
