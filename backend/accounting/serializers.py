from rest_framework import serializers
from .models import (
    Account, Transaction, TransactionEntry, Budget, BudgetItem,
    Invoice, InvoiceItem, FixedAsset, TaxRate, Payment,
    RecurringInvoice, RecurringInvoiceItem
)

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class TransactionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionEntry
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    entries = TransactionEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by', 'approved_by')

class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        fields = '__all__'

class BudgetSerializer(serializers.ModelSerializer):
    items = BudgetItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class FixedAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixedAsset
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class RecurringInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringInvoiceItem
        fields = '__all__'

class RecurringInvoiceSerializer(serializers.ModelSerializer):
    items = RecurringInvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = RecurringInvoice
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by') 