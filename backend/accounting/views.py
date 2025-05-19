from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
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

# Create your views here.

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    @transaction.atomic
    def perform_create(self, serializer):
        transaction_obj = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle transaction entries from the request data
        entries_data = self.request.data.get('entries', [])
        for entry_data in entries_data:
            entry_data['transaction'] = transaction_obj.id
            entry_serializer = TransactionEntrySerializer(data=entry_data)
            entry_serializer.is_valid(raise_exception=True)
            entry_serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        transaction_obj = self.get_object()
        if transaction_obj.status == 'draft':
            transaction_obj.status = 'approved'
            transaction_obj.approved_by = request.user
            transaction_obj.save()
            return Response({'status': 'transaction approved'})
        return Response(
            {'error': 'Cannot approve transaction'},
            status=status.HTTP_400_BAD_REQUEST
        )

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    @transaction.atomic
    def perform_create(self, serializer):
        budget = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle budget items from the request data
        items_data = self.request.data.get('items', [])
        for item_data in items_data:
            item_data['budget'] = budget.id
            item_serializer = BudgetItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    @transaction.atomic
    def perform_create(self, serializer):
        invoice = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle invoice items from the request data
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
        if invoice.status == 'draft':
            invoice.status = 'sent'
            invoice.save()
            # TODO: Implement email sending logic
            return Response({'status': 'invoice sent'})
        return Response(
            {'error': 'Cannot send invoice'},
            status=status.HTTP_400_BAD_REQUEST
        )

class FixedAssetViewSet(viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def calculate_depreciation(self, request, pk=None):
        asset = self.get_object()
        date = request.data.get('date')
        if not date:
            return Response(
                {'error': 'Date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        depreciation = asset.calculate_depreciation(date)
        return Response({'depreciation': depreciation})

class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )

class RecurringInvoiceViewSet(viewsets.ModelViewSet):
    queryset = RecurringInvoice.objects.all()
    serializer_class = RecurringInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user.organization)

    @transaction.atomic
    def perform_create(self, serializer):
        recurring_invoice = serializer.save(
            organization=self.request.user.organization,
            created_by=self.request.user
        )
        
        # Handle recurring invoice items from the request data
        items_data = self.request.data.get('items', [])
        for item_data in items_data:
            item_data['recurring_invoice'] = recurring_invoice.id
            item_serializer = RecurringInvoiceItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()

    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        recurring_invoice = self.get_object()
        invoice = recurring_invoice.generate_invoice()
        recurring_invoice.update_next_date()
        return Response(InvoiceSerializer(invoice).data)
