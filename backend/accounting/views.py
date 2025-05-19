from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
from .models import (
    Account, Transaction, TransactionEntry, Budget, BudgetItem,
    Invoice, InvoiceItem, FixedAsset, TaxRate, Payment,
    RecurringInvoice, RecurringInvoiceItem
)
from .serializers import (
    AccountSerializer, TransactionSerializer, TransactionEntrySerializer,
    BudgetSerializer, BudgetItemSerializer, InvoiceSerializer,
    InvoiceItemSerializer, FixedAssetSerializer, TaxRateSerializer,
    PaymentSerializer, RecurringInvoiceSerializer, RecurringInvoiceItemSerializer
)
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, F, Q, Case, When, Value, DecimalField
from django.db.models.functions import Coalesce, ExtractYear, ExtractMonth
import csv
import io

# Create your views here.

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'account_type', 'current_balance']
    ordering = ['code']

    def get_queryset(self):
        queryset = Account.objects.filter(organization=self.request.user.organization)
        account_type = self.request.query_params.get('account_type', None)
        subtype = self.request.query_params.get('subtype', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        if subtype:
            queryset = queryset.filter(subtype=subtype)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        account = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        entries = account.entries.all()
        if start_date:
            entries = entries.filter(transaction__date__gte=start_date)
        if end_date:
            entries = entries.filter(transaction__date__lte=end_date)
            
        entries = entries.select_related('transaction').order_by('transaction__date')
        
        data = {
            'transactions': TransactionEntrySerializer(entries, many=True).data,
            'total_debit': entries.filter(amount__gt=0).aggregate(total=Sum('amount'))['total'] or 0,
            'total_credit': entries.filter(amount__lt=0).aggregate(total=Sum('amount'))['total'] or 0
        }
        return Response(data)

    @action(detail=True, methods=['get'])
    def balance_sheet(self, request, pk=None):
        account = self.get_object()
        date = request.query_params.get('date', date.today())
        
        balance = account.entries.filter(
            transaction__date__lte=date,
            transaction__status='posted'
        ).aggregate(balance=Sum('amount'))['balance'] or 0
        
        return Response({
            'balance': balance,
            'date': date
        })

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'reference']
    ordering_fields = ['date', 'created_at', 'status']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            organization=self.request.user.organization
        )
        status = self.request.query_params.get('status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        transaction_obj = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle transaction entries
        entries_data = self.request.data.get('entries', [])
        total = Decimal('0')
        
        for entry_data in entries_data:
            entry_data['transaction'] = transaction_obj.id
            entry_serializer = TransactionEntrySerializer(data=entry_data)
            entry_serializer.is_valid(raise_exception=True)
            entry_serializer.save()
            total += Decimal(str(entry_data['amount']))
        
        if abs(total) > 0.01:  # Allow for small rounding differences
            raise serializers.ValidationError(
                _("Transaction must be balanced (debits = credits)")
            )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        transaction_obj = self.get_object()
        
        if not transaction_obj.is_balanced():
            return Response(
                {'error': _("Cannot approve unbalanced transaction")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if transaction_obj.status != 'draft':
            return Response(
                {'error': _("Only draft transactions can be approved")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        transaction_obj.status = 'approved'
        transaction_obj.approved_by = request.user
        transaction_obj.save()
        
        return Response({'status': 'transaction approved'})

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        transaction_obj = self.get_object()
        
        if transaction_obj.status != 'approved':
            return Response(
                {'error': _("Only approved transactions can be posted")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        transaction_obj.status = 'posted'
        transaction_obj.save()
        
        # Update account balances
        for entry in transaction_obj.entries.all():
            entry.account.update_balance(entry.amount)
        
        return Response({'status': 'transaction posted'})

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        transaction_obj = self.get_object()
        
        if transaction_obj.status not in ['draft', 'approved']:
            return Response(
                {'error': _("Cannot void posted or reconciled transactions")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        transaction_obj.status = 'void'
        transaction_obj.save()
        
        return Response({'status': 'transaction voided'})

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = Budget.objects.filter(
            organization=self.request.user.organization
        )
        is_active = self.request.query_params.get('is_active', None)
        period = self.request.query_params.get('period', None)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        if period:
            queryset = queryset.filter(period=period)
            
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        budget = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle budget items
        items_data = self.request.data.get('items', [])
        for item_data in items_data:
            item_data['budget'] = budget.id
            item_serializer = BudgetItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        budget = self.get_object()
        items = budget.items.all()
        
        performance_data = {
            'total_budget': sum(item.amount for item in items),
            'total_actual': sum(item.actual_amount for item in items),
            'total_variance': sum(item.variance for item in items),
            'items': []
        }
        
        for item in items:
            performance_data['items'].append({
                'account': item.account.name,
                'budget': item.amount,
                'actual': item.actual_amount,
                'variance': item.variance,
                'variance_percentage': (
                    (item.variance / item.amount * 100)
                    if item.amount != 0 else 0
                )
            })
        
        return Response(performance_data)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['number', 'reference', 'party_name', 'party_tax_id']
    ordering_fields = ['date', 'due_date', 'total', 'status']
    ordering = ['-date']

    def get_queryset(self):
        queryset = Invoice.objects.filter(
            organization=self.request.user.organization
        )
        status = self.request.query_params.get('status', None)
        type = self.request.query_params.get('type', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if type:
            queryset = queryset.filter(type=type)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        invoice = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle invoice items
        items_data = self.request.data.get('items', [])
        for item_data in items_data:
            item_data['invoice'] = invoice.id
            item_serializer = InvoiceItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()
        
        invoice.calculate_totals()

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        invoice = self.get_object()
        
        if invoice.status != 'draft':
            return Response(
                {'error': _("Only draft invoices can be sent")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not invoice.items.exists():
            return Response(
                {'error': _("Cannot send invoice without items")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        invoice.status = 'sent'
        invoice.save()
        
        # TODO: Implement email sending logic
        
        return Response({'status': 'invoice sent'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        
        if invoice.status in ['paid', 'cancelled']:
            return Response(
                {'error': _("Cannot cancel paid or already cancelled invoices")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        invoice.status = 'cancelled'
        invoice.save()
        
        return Response({'status': 'invoice cancelled'})

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        invoice = self.get_object()
        payments = invoice.payments.all().order_by('-date')
        
        return Response({
            'payments': PaymentSerializer(payments, many=True).data,
            'total_paid': invoice.amount_paid,
            'balance_due': invoice.balance_due
        })

class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'asset_number', 'description']
    ordering_fields = ['purchase_date', 'current_value', 'status']
    ordering = ['-purchase_date']

    def get_queryset(self):
        queryset = FixedAsset.objects.filter(
            organization=self.request.user.organization
        )
        status = self.request.query_params.get('status', None)
        location = self.request.query_params.get('location', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if location:
            queryset = queryset.filter(location=location)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def dispose(self, request, pk=None):
        asset = self.get_object()
        disposal_date = request.data.get('date', date.today())
        disposal_value = request.data.get('value', 0)
        
        if asset.status != 'active':
            return Response(
                {'error': _("Can only dispose active assets")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        asset.status = 'disposed'
        asset.current_value = disposal_value
        asset.save()
        
        # TODO: Create disposal transaction
        
        return Response({
            'status': 'asset disposed',
            'disposal_value': disposal_value
        })

    @action(detail=True, methods=['get'])
    def depreciation_schedule(self, request, pk=None):
        asset = self.get_object()
        end_date = request.query_params.get('end_date', None)
        
        schedule = asset.calculate_depreciation(
            end_date or (asset.purchase_date + timedelta(days=365*asset.useful_life_years))
        )
        
        return Response(schedule)

class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'rate']
    ordering = ['name']

    def get_queryset(self):
        queryset = TaxRate.objects.filter(
            organization=self.request.user.organization
        )
        is_active = self.request.query_params.get('is_active', None)
        is_compound = self.request.query_params.get('is_compound', None)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        if is_compound is not None:
            queryset = queryset.filter(is_compound=is_compound == 'true')
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference', 'transaction_id', 'check_number']
    ordering_fields = ['date', 'amount', 'status']
    ordering = ['-date']

    def get_queryset(self):
        queryset = Payment.objects.filter(
            organization=self.request.user.organization
        )
        status = self.request.query_params.get('status', None)
        method = self.request.query_params.get('method', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if status:
            queryset = queryset.filter(status=status)
        if method:
            queryset = queryset.filter(method=method)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        payment = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Update invoice paid amount
        invoice = payment.invoice
        invoice.amount_paid = invoice.payments.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        if invoice.amount_paid >= invoice.total:
            invoice.status = 'paid'
        elif invoice.amount_paid > 0:
            invoice.status = 'partially_paid'
            
        invoice.save()

    @action(detail=True, methods=['post'])
    def void(self, request, pk=None):
        payment = self.get_object()
        
        if payment.status == 'voided':
            return Response(
                {'error': _("Payment is already voided")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        payment.status = 'voided'
        payment.save()
        
        # Update invoice status
        invoice = payment.invoice
        invoice.amount_paid = invoice.payments.exclude(
            status='voided'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if invoice.amount_paid >= invoice.total:
            invoice.status = 'paid'
        elif invoice.amount_paid > 0:
            invoice.status = 'partially_paid'
        else:
            invoice.status = 'sent'
            
        invoice.save()
        
        return Response({'status': 'payment voided'})

class RecurringInvoiceViewSet(viewsets.ModelViewSet):
    queryset = RecurringInvoice.objects.all()
    serializer_class = RecurringInvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'party_name']
    ordering_fields = ['name', 'next_date', 'frequency']
    ordering = ['next_date']

    def get_queryset(self):
        queryset = RecurringInvoice.objects.filter(
            organization=self.request.user.organization
        )
        is_active = self.request.query_params.get('is_active', None)
        frequency = self.request.query_params.get('frequency', None)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
            
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        recurring_invoice = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle recurring invoice items
        items_data = self.request.data.get('items', [])
        for item_data in items_data:
            item_data['recurring_invoice'] = recurring_invoice.id
            item_serializer = RecurringInvoiceItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()

    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        recurring_invoice = self.get_object()
        
        if not recurring_invoice.is_active:
            return Response(
                {'error': _("Cannot generate invoice from inactive template")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if recurring_invoice.end_date and recurring_invoice.end_date < date.today():
            return Response(
                {'error': _("Recurring invoice has ended")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        invoice = recurring_invoice.generate_invoice()
        recurring_invoice.update_next_date()
        
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['get'])
    def preview_next(self, request, pk=None):
        recurring_invoice = self.get_object()
        next_date = recurring_invoice.next_date
        
        if not next_date:
            return Response(
                {'error': _("No next date available")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            'next_date': next_date,
            'due_date': next_date + timedelta(days=recurring_invoice.days_due),
            'items': RecurringInvoiceItemSerializer(
                recurring_invoice.items.all(),
                many=True
            ).data
        })

class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date = request.query_params.get('date', date.today())
        organization = request.user.organization
        
        # Get all accounts
        accounts = Account.objects.filter(
            organization=organization,
            is_active=True
        ).exclude(account_type='income').exclude(account_type='expense')
        
        # Calculate balances
        assets = []
        liabilities = []
        equity = []
        
        for account in accounts:
            balance = account.entries.filter(
                transaction__date__lte=date,
                transaction__status='posted'
            ).aggregate(balance=Coalesce(Sum('amount'), 0))['balance']
            
            account_data = {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'balance': balance
            }
            
            if account.account_type == 'asset':
                assets.append(account_data)
            elif account.account_type == 'liability':
                liabilities.append(account_data)
            else:  # equity
                equity.append(account_data)
        
        # Calculate totals
        total_assets = sum(account['balance'] for account in assets)
        total_liabilities = sum(account['balance'] for account in liabilities)
        total_equity = sum(account['balance'] for account in equity)
        
        return Response({
            'date': date,
            'assets': {
                'accounts': assets,
                'total': total_assets
            },
            'liabilities': {
                'accounts': liabilities,
                'total': total_liabilities
            },
            'equity': {
                'accounts': equity,
                'total': total_equity
            },
            'total_liabilities_and_equity': total_liabilities + total_equity
        })

class IncomeStatementView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', date.today())
        organization = request.user.organization
        
        # Get income and expense accounts
        accounts = Account.objects.filter(
            organization=organization,
            is_active=True,
            account_type__in=['income', 'expense']
        )
        
        # Calculate balances
        income = []
        expenses = []
        
        for account in accounts:
            query = Q(
                transaction__status='posted',
                transaction__date__lte=end_date
            )
            if start_date:
                query &= Q(transaction__date__gte=start_date)
            
            balance = account.entries.filter(query).aggregate(
                balance=Coalesce(Sum('amount'), 0)
            )['balance']
            
            account_data = {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'balance': abs(balance)  # Show positive numbers
            }
            
            if account.account_type == 'income':
                income.append(account_data)
            else:  # expense
                expenses.append(account_data)
        
        # Calculate totals
        total_income = sum(account['balance'] for account in income)
        total_expenses = sum(account['balance'] for account in expenses)
        net_income = total_income - total_expenses
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'income': {
                'accounts': income,
                'total': total_income
            },
            'expenses': {
                'accounts': expenses,
                'total': total_expenses
            },
            'net_income': net_income
        })

class CashFlowStatementView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', date.today())
        organization = request.user.organization
        
        # Get cash accounts
        cash_accounts = Account.objects.filter(
            organization=organization,
            account_type='asset',
            subtype__in=['cash', 'bank']
        )
        
        operating_activities = []
        investing_activities = []
        financing_activities = []
        
        for account in cash_accounts:
            query = Q(
                transaction__status='posted',
                transaction__date__lte=end_date
            )
            if start_date:
                query &= Q(transaction__date__gte=start_date)
            
            entries = account.entries.filter(query).select_related('transaction')
            
            for entry in entries:
                flow_data = {
                    'date': entry.transaction.date,
                    'description': entry.transaction.description,
                    'amount': entry.amount
                }
                
                # Classify the cash flow
                # This is a simplified classification
                if entry.transaction.tags and 'type' in entry.transaction.tags:
                    flow_type = entry.transaction.tags['type']
                    if flow_type == 'operating':
                        operating_activities.append(flow_data)
                    elif flow_type == 'investing':
                        investing_activities.append(flow_data)
                    elif flow_type == 'financing':
                        financing_activities.append(flow_data)
                else:
                    # Default to operating activities
                    operating_activities.append(flow_data)
        
        # Calculate totals
        total_operating = sum(activity['amount'] for activity in operating_activities)
        total_investing = sum(activity['amount'] for activity in investing_activities)
        total_financing = sum(activity['amount'] for activity in financing_activities)
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'operating_activities': {
                'items': operating_activities,
                'total': total_operating
            },
            'investing_activities': {
                'items': investing_activities,
                'total': total_investing
            },
            'financing_activities': {
                'items': financing_activities,
                'total': total_financing
            },
            'net_cash_flow': total_operating + total_investing + total_financing
        })

class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date = request.query_params.get('date', date.today())
        organization = request.user.organization
        
        accounts = Account.objects.filter(
            organization=organization,
            is_active=True
        )
        
        trial_balance = []
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for account in accounts:
            entries = account.entries.filter(
                transaction__date__lte=date,
                transaction__status='posted'
            )
            
            debits = entries.filter(amount__gt=0).aggregate(
                total=Coalesce(Sum('amount'), 0)
            )['total']
            
            credits = abs(entries.filter(amount__lt=0).aggregate(
                total=Coalesce(Sum('amount'), 0)
            )['total'])
            
            if debits > 0 or credits > 0:
                trial_balance.append({
                    'account_id': account.id,
                    'account_code': account.code,
                    'account_name': account.name,
                    'debits': debits,
                    'credits': credits
                })
                
                total_debits += debits
                total_credits += credits
        
        return Response({
            'date': date,
            'accounts': trial_balance,
            'totals': {
                'debits': total_debits,
                'credits': total_credits,
                'difference': total_debits - total_credits
            }
        })

class AgedReceivablesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        as_of_date = request.query_params.get('date', date.today())
        organization = request.user.organization
        
        # Get all unpaid sales invoices
        invoices = Invoice.objects.filter(
            organization=organization,
            type='sale',
            status__in=['sent', 'partially_paid'],
            date__lte=as_of_date
        ).annotate(
            days_overdue=ExtractDay(Value(as_of_date) - F('due_date')),
            balance_due=F('total') - F('amount_paid')
        )
        
        # Age brackets
        current = []
        days_1_30 = []
        days_31_60 = []
        days_61_90 = []
        days_over_90 = []
        
        for invoice in invoices:
            data = {
                'invoice_number': invoice.number,
                'party_name': invoice.party_name,
                'date': invoice.date,
                'due_date': invoice.due_date,
                'total': invoice.total,
                'balance_due': invoice.balance_due,
                'days_overdue': max(0, invoice.days_overdue)
            }
            
            if invoice.days_overdue <= 0:
                current.append(data)
            elif invoice.days_overdue <= 30:
                days_1_30.append(data)
            elif invoice.days_overdue <= 60:
                days_31_60.append(data)
            elif invoice.days_overdue <= 90:
                days_61_90.append(data)
            else:
                days_over_90.append(data)
        
        return Response({
            'as_of_date': as_of_date,
            'aging': {
                'current': {
                    'invoices': current,
                    'total': sum(inv['balance_due'] for inv in current)
                },
                '1-30_days': {
                    'invoices': days_1_30,
                    'total': sum(inv['balance_due'] for inv in days_1_30)
                },
                '31-60_days': {
                    'invoices': days_31_60,
                    'total': sum(inv['balance_due'] for inv in days_31_60)
                },
                '61-90_days': {
                    'invoices': days_61_90,
                    'total': sum(inv['balance_due'] for inv in days_61_90)
                },
                'over_90_days': {
                    'invoices': days_over_90,
                    'total': sum(inv['balance_due'] for inv in days_over_90)
                }
            },
            'total_receivables': sum(
                inv.balance_due for inv in invoices
            )
        })

class AgedPayablesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        as_of_date = request.query_params.get('date', date.today())
        organization = request.user.organization
        
        # Get all unpaid purchase invoices
        invoices = Invoice.objects.filter(
            organization=organization,
            type='purchase',
            status__in=['sent', 'partially_paid'],
            date__lte=as_of_date
        ).annotate(
            days_overdue=ExtractDay(Value(as_of_date) - F('due_date')),
            balance_due=F('total') - F('amount_paid')
        )
        
        # Age brackets (same as receivables)
        current = []
        days_1_30 = []
        days_31_60 = []
        days_61_90 = []
        days_over_90 = []
        
        for invoice in invoices:
            data = {
                'invoice_number': invoice.number,
                'party_name': invoice.party_name,
                'date': invoice.date,
                'due_date': invoice.due_date,
                'total': invoice.total,
                'balance_due': invoice.balance_due,
                'days_overdue': max(0, invoice.days_overdue)
            }
            
            if invoice.days_overdue <= 0:
                current.append(data)
            elif invoice.days_overdue <= 30:
                days_1_30.append(data)
            elif invoice.days_overdue <= 60:
                days_31_60.append(data)
            elif invoice.days_overdue <= 90:
                days_61_90.append(data)
            else:
                days_over_90.append(data)
        
        return Response({
            'as_of_date': as_of_date,
            'aging': {
                'current': {
                    'invoices': current,
                    'total': sum(inv['balance_due'] for inv in current)
                },
                '1-30_days': {
                    'invoices': days_1_30,
                    'total': sum(inv['balance_due'] for inv in days_1_30)
                },
                '31-60_days': {
                    'invoices': days_31_60,
                    'total': sum(inv['balance_due'] for inv in days_31_60)
                },
                '61-90_days': {
                    'invoices': days_61_90,
                    'total': sum(inv['balance_due'] for inv in days_61_90)
                },
                'over_90_days': {
                    'invoices': days_over_90,
                    'total': sum(inv['balance_due'] for inv in days_over_90)
                }
            },
            'total_payables': sum(
                inv.balance_due for inv in invoices
            )
        })

class BudgetVsActualView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        budget_id = request.query_params.get('budget_id')
        organization = request.user.organization
        
        if not budget_id:
            # Get the current active budget
            budget = Budget.objects.filter(
                organization=organization,
                is_active=True,
                start_date__lte=date.today(),
                end_date__gte=date.today()
            ).first()
            
            if not budget:
                return Response(
                    {'error': _("No active budget found")},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            budget = Budget.objects.filter(
                organization=organization,
                id=budget_id
            ).first()
            
            if not budget:
                return Response(
                    {'error': _("Budget not found")},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get budget items with actual amounts
        items = []
        total_budget = Decimal('0')
        total_actual = Decimal('0')
        
        for item in budget.items.all():
            actual_amount = item.account.entries.filter(
                transaction__status='posted',
                transaction__date__gte=budget.start_date,
                transaction__date__lte=budget.end_date
            ).aggregate(
                total=Coalesce(Sum('amount'), 0)
            )['total']
            
            variance = item.amount - actual_amount
            variance_percentage = (
                (variance / item.amount * 100)
                if item.amount != 0 else 0
            )
            
            items.append({
                'account_code': item.account.code,
                'account_name': item.account.name,
                'budget_amount': item.amount,
                'actual_amount': actual_amount,
                'variance': variance,
                'variance_percentage': variance_percentage
            })
            
            total_budget += item.amount
            total_actual += actual_amount
        
        total_variance = total_budget - total_actual
        total_variance_percentage = (
            (total_variance / total_budget * 100)
            if total_budget != 0 else 0
        )
        
        return Response({
            'budget': {
                'id': budget.id,
                'name': budget.name,
                'period': budget.period,
                'start_date': budget.start_date,
                'end_date': budget.end_date
            },
            'items': items,
            'totals': {
                'budget': total_budget,
                'actual': total_actual,
                'variance': total_variance,
                'variance_percentage': total_variance_percentage
            }
        })

class TaxSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', date.today())
        organization = request.user.organization
        
        # Get all tax rates
        tax_rates = TaxRate.objects.filter(
            organization=organization,
            is_active=True
        )
        
        summary = []
        total_tax_collected = Decimal('0')
        total_tax_paid = Decimal('0')
        
        for tax_rate in tax_rates:
            # Sales tax collected
            sales_tax = InvoiceItem.objects.filter(
                invoice__organization=organization,
                invoice__type='sale',
                invoice__status__in=['sent', 'paid', 'partially_paid'],
                invoice__date__lte=end_date,
                tax_rate=tax_rate.rate
            )
            
            if start_date:
                sales_tax = sales_tax.filter(invoice__date__gte=start_date)
            
            tax_collected = sales_tax.aggregate(
                tax=Sum(F('quantity') * F('unit_price') * F('tax_rate') / 100)
            )['tax'] or 0
            
            # Purchase tax paid
            purchase_tax = InvoiceItem.objects.filter(
                invoice__organization=organization,
                invoice__type='purchase',
                invoice__status__in=['sent', 'paid', 'partially_paid'],
                invoice__date__lte=end_date,
                tax_rate=tax_rate.rate
            )
            
            if start_date:
                purchase_tax = purchase_tax.filter(invoice__date__gte=start_date)
            
            tax_paid = purchase_tax.aggregate(
                tax=Sum(F('quantity') * F('unit_price') * F('tax_rate') / 100)
            )['tax'] or 0
            
            summary.append({
                'tax_rate': {
                    'id': tax_rate.id,
                    'name': tax_rate.name,
                    'rate': tax_rate.rate,
                    'is_recoverable': tax_rate.is_recoverable
                },
                'tax_collected': tax_collected,
                'tax_paid': tax_paid,
                'net_tax': tax_collected - (
                    tax_paid if tax_rate.is_recoverable else 0
                )
            })
            
            total_tax_collected += tax_collected
            total_tax_paid += tax_paid if tax_rate.is_recoverable else 0
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'tax_rates': summary,
            'totals': {
                'tax_collected': total_tax_collected,
                'tax_paid': total_tax_paid,
                'net_tax_payable': total_tax_collected - total_tax_paid
            }
        })

class AccountReconciliationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        account = get_object_or_404(Account, pk=pk, organization=request.user.organization)
        
        # Get reconciliation data
        statement_balance = Decimal(request.data.get('statement_balance', 0))
        statement_date = request.data.get('statement_date', date.today())
        reconciled_items = request.data.get('reconciled_items', [])
        
        # Mark entries as reconciled
        for item in reconciled_items:
            entry = get_object_or_404(
                TransactionEntry,
                id=item['entry_id'],
                account=account
            )
            entry.reconciled = True
            entry.reconciled_date = statement_date
            entry.save()
        
        # Calculate reconciled balance
        reconciled_balance = account.entries.filter(
            transaction__date__lte=statement_date,
            reconciled=True
        ).aggregate(
            balance=Coalesce(Sum('amount'), 0)
        )['balance']
        
        # Calculate unreconciled items
        unreconciled_items = account.entries.filter(
            transaction__date__lte=statement_date,
            reconciled=False
        ).values(
            'id',
            'transaction__date',
            'transaction__description',
            'amount'
        )
        
        return Response({
            'account': {
                'id': account.id,
                'name': account.name,
                'balance': account.current_balance
            },
            'statement_date': statement_date,
            'statement_balance': statement_balance,
            'reconciled_balance': reconciled_balance,
            'difference': statement_balance - reconciled_balance,
            'unreconciled_items': unreconciled_items
        })

class TransactionImportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': _("No file provided")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': _("File must be a CSV")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process CSV file
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(decoded_file))
        
        transactions = []
        errors = []
        
        for row in csv_data:
            try:
                with transaction.atomic():
                    # Create transaction
                    trans = Transaction.objects.create(
                        organization=request.user.organization,
                        date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                        description=row['description'],
                        reference=row.get('reference', ''),
                        created_by=request.user
                    )
                    
                    # Create entries
                    debit_account = Account.objects.get(
                        organization=request.user.organization,
                        code=row['debit_account']
                    )
                    credit_account = Account.objects.get(
                        organization=request.user.organization,
                        code=row['credit_account']
                    )
                    
                    amount = Decimal(row['amount'])
                    
                    TransactionEntry.objects.create(
                        transaction=trans,
                        account=debit_account,
                        amount=amount
                    )
                    
                    TransactionEntry.objects.create(
                        transaction=trans,
                        account=credit_account,
                        amount=-amount
                    )
                    
                    transactions.append(trans.id)
            
            except Exception as e:
                errors.append({
                    'row': row,
                    'error': str(e)
                })
        
        return Response({
            'imported_transactions': transactions,
            'errors': errors
        })

class TransactionExportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', date.today())
        
        # Get transactions
        transactions = Transaction.objects.filter(
            organization=request.user.organization,
            date__lte=end_date
        )
        
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        
        # Create CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date',
            'Description',
            'Reference',
            'Status',
            'Account Code',
            'Account Name',
            'Debit',
            'Credit'
        ])
        
        # Write transactions
        for trans in transactions:
            for entry in trans.entries.all():
                writer.writerow([
                    trans.date,
                    trans.description,
                    trans.reference,
                    trans.status,
                    entry.account.code,
                    entry.account.name,
                    entry.amount if entry.amount > 0 else '',
                    -entry.amount if entry.amount < 0 else ''
                ])
        
        return Response({
            'content': output.getvalue(),
            'filename': f'transactions_{start_date}_{end_date}.csv'
        })

class GenerateRecurringInvoicesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        organization = request.user.organization
        
        # Get all active recurring invoices due for generation
        recurring_invoices = RecurringInvoice.objects.filter(
            organization=organization,
            is_active=True,
            next_date__lte=date.today()
        ).exclude(
            end_date__lt=date.today()
        )
        
        generated_invoices = []
        errors = []
        
        for recurring in recurring_invoices:
            try:
                invoice = recurring.generate_invoice()
                recurring.update_next_date()
                generated_invoices.append(invoice.id)
                
                if recurring.auto_send:
                    invoice.status = 'sent'
                    invoice.save()
                    # TODO: Implement email sending logic
            
            except Exception as e:
                errors.append({
                    'recurring_invoice_id': recurring.id,
                    'error': str(e)
                })
        
        return Response({
            'generated_invoices': generated_invoices,
            'errors': errors
        })

class GenerateFinancialStatementsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        organization = request.user.organization
        date = request.data.get('date', date.today())
        report_types = request.data.get('report_types', [
            'balance_sheet',
            'income_statement',
            'cash_flow'
        ])
        
        reports = {}
        
        if 'balance_sheet' in report_types:
            balance_sheet_view = BalanceSheetView()
            reports['balance_sheet'] = balance_sheet_view.get(
                request._request
            ).data
        
        if 'income_statement' in report_types:
            income_statement_view = IncomeStatementView()
            reports['income_statement'] = income_statement_view.get(
                request._request
            ).data
        
        if 'cash_flow' in report_types:
            cash_flow_view = CashFlowStatementView()
            reports['cash_flow'] = cash_flow_view.get(
                request._request
            ).data
        
        # TODO: Generate PDF reports
        
        return Response(reports)
