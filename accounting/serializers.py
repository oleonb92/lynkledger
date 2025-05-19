from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from decimal import Decimal
from .models import (
    Account, Transaction, TransactionEntry, Budget, BudgetItem,
    Invoice, InvoiceItem, FixedAsset, TaxRate, Payment,
    RecurringInvoice, RecurringInvoiceItem
)

class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        source='current_balance',
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    child_accounts = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = (
            'id', 'organization', 'name', 'code', 'description',
            'account_type', 'subtype', 'parent', 'balance',
            'available_balance', 'currency', 'is_active',
            'is_archived', 'child_accounts', 'created_at',
            'updated_at', 'created_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def get_child_accounts(self, obj):
        return AccountSerializer(obj.children.all(), many=True).data

    def validate(self, data):
        # Validate account type and subtype combination
        account_type = data.get('account_type')
        subtype = data.get('subtype')
        
        if subtype:
            valid_subtypes = {
                'asset': ['cash', 'bank', 'receivable', 'inventory', 'fixed_asset'],
                'liability': ['payable', 'credit_card', 'loan'],
                'income': ['sales', 'service', 'interest'],
                'expense': ['cost_of_goods', 'operating', 'payroll', 'tax']
            }
            
            if account_type in valid_subtypes and subtype not in valid_subtypes[account_type]:
                raise serializers.ValidationError(
                    _("Invalid subtype for account type")
                )
        
        return data

class TransactionEntrySerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = TransactionEntry
        fields = (
            'id', 'transaction', 'account', 'account_name',
            'description', 'amount', 'tax_rate', 'currency',
            'exchange_rate'
        )

    def validate(self, data):
        if data['amount'] == 0:
            raise serializers.ValidationError(
                _("Amount cannot be zero")
            )
        return data

class TransactionSerializer(serializers.ModelSerializer):
    entries = TransactionEntrySerializer(many=True)
    total_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    is_balanced = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'organization', 'date', 'description',
            'reference', 'status', 'is_recurring',
            'recurrence_type', 'recurrence_end_date',
            'entries', 'total_amount', 'is_balanced',
            'tags', 'created_at', 'updated_at',
            'created_by', 'approved_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by', 'approved_by')

    def validate(self, data):
        entries = self.initial_data.get('entries', [])
        if not entries:
            raise serializers.ValidationError(
                _("At least one entry is required")
            )
        
        total = sum(Decimal(str(entry['amount'])) for entry in entries)
        if abs(total) > 0.01:  # Allow for small rounding differences
            raise serializers.ValidationError(
                _("Transaction must be balanced (debits = credits)")
            )
        
        return data

    def create(self, validated_data):
        entries_data = validated_data.pop('entries')
        transaction = Transaction.objects.create(**validated_data)
        
        for entry_data in entries_data:
            TransactionEntry.objects.create(transaction=transaction, **entry_data)
        
        return transaction

    def update(self, instance, validated_data):
        entries_data = validated_data.pop('entries')
        
        # Update transaction fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle entries
        instance.entries.all().delete()
        for entry_data in entries_data:
            TransactionEntry.objects.create(transaction=instance, **entry_data)
        
        return instance

class BudgetItemSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    actual_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    variance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = BudgetItem
        fields = (
            'id', 'budget', 'account', 'account_name',
            'amount', 'minimum_amount', 'maximum_amount',
            'actual_amount', 'variance', 'notes'
        )

    def validate(self, data):
        min_amount = data.get('minimum_amount')
        max_amount = data.get('maximum_amount')
        amount = data.get('amount')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise serializers.ValidationError(
                _("Minimum amount cannot be greater than maximum amount")
            )
        
        if amount:
            if min_amount and amount < min_amount:
                raise serializers.ValidationError(
                    _("Amount cannot be less than minimum amount")
                )
            if max_amount and amount > max_amount:
                raise serializers.ValidationError(
                    _("Amount cannot be greater than maximum amount")
                )
        
        return data

class BudgetSerializer(serializers.ModelSerializer):
    items = BudgetItemSerializer(many=True)
    total_budget = serializers.SerializerMethodField()
    total_actual = serializers.SerializerMethodField()
    total_variance = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = (
            'id', 'organization', 'name', 'description',
            'start_date', 'end_date', 'period', 'items',
            'total_budget', 'total_actual', 'total_variance',
            'is_active', 'created_at', 'updated_at', 'created_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def get_total_budget(self, obj):
        return obj.items.aggregate(total=Sum('amount'))['total'] or 0

    def get_total_actual(self, obj):
        return sum(item.actual_amount for item in obj.items.all())

    def get_total_variance(self, obj):
        return sum(item.variance for item in obj.items.all())

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                _("End date must be after start date")
            )
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        budget = Budget.objects.create(**validated_data)
        
        for item_data in items_data:
            BudgetItem.objects.create(budget=budget, **item_data)
        
        return budget

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        
        # Update budget fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle items
        instance.items.all().delete()
        for item_data in items_data:
            BudgetItem.objects.create(budget=instance, **item_data)
        
        return instance

class InvoiceItemSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    tax_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = InvoiceItem
        fields = (
            'id', 'invoice', 'description', 'quantity',
            'unit_price', 'discount_rate', 'tax_rate',
            'amount', 'tax_amount', 'income_account',
            'tax_account'
        )

    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError(
                _("Quantity must be greater than zero")
            )
        if data['unit_price'] < 0:
            raise serializers.ValidationError(
                _("Unit price cannot be negative")
            )
        if data['discount_rate'] < 0 or data['discount_rate'] > 100:
            raise serializers.ValidationError(
                _("Discount rate must be between 0 and 100")
            )
        if data['tax_rate'] < 0:
            raise serializers.ValidationError(
                _("Tax rate cannot be negative")
            )
        return data

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    balance_due = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    is_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = (
            'id', 'organization', 'type', 'number',
            'reference', 'date', 'due_date', 'party_name',
            'party_tax_id', 'party_address', 'party_email',
            'party_phone', 'subtotal', 'tax_amount',
            'total', 'amount_paid', 'balance_due',
            'is_paid', 'currency', 'exchange_rate',
            'notes', 'terms', 'status', 'items',
            'created_at', 'updated_at', 'created_by'
        )
        read_only_fields = (
            'created_at', 'updated_at', 'created_by',
            'subtotal', 'tax_amount', 'total', 'amount_paid'
        )

    def validate(self, data):
        if data['date'] > data['due_date']:
            raise serializers.ValidationError(
                _("Due date cannot be before invoice date")
            )
        
        items = self.initial_data.get('items', [])
        if not items:
            raise serializers.ValidationError(
                _("At least one item is required")
            )
        
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        invoice.calculate_totals()
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle items
        instance.items.all().delete()
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=instance, **item_data)
        
        instance.calculate_totals()
        return instance

class FixedAssetSerializer(serializers.ModelSerializer):
    depreciation_schedule = serializers.SerializerMethodField()
    
    class Meta:
        model = FixedAsset
        fields = (
            'id', 'organization', 'name', 'description',
            'asset_number', 'purchase_date', 'purchase_cost',
            'useful_life_years', 'salvage_value',
            'depreciation_method', 'status', 'current_value',
            'accumulated_depreciation', 'location',
            'custodian', 'insurance_policy',
            'insurance_expiry', 'depreciation_schedule',
            'created_at', 'updated_at', 'created_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def get_depreciation_schedule(self, obj):
        return obj.calculate_depreciation(obj.purchase_date)

    def validate(self, data):
        if data['salvage_value'] >= data['purchase_cost']:
            raise serializers.ValidationError(
                _("Salvage value cannot be greater than purchase cost")
            )
        if data['useful_life_years'] <= 0:
            raise serializers.ValidationError(
                _("Useful life must be greater than zero")
            )
        return data

class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = (
            'id', 'organization', 'name', 'description',
            'rate', 'is_compound', 'is_recoverable',
            'sales_tax_account', 'purchase_tax_account',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        if data['rate'] < 0:
            raise serializers.ValidationError(
                _("Tax rate cannot be negative")
            )
        return data

class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    party_name = serializers.CharField(source='invoice.party_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id', 'organization', 'invoice', 'invoice_number',
            'party_name', 'date', 'amount', 'currency',
            'exchange_rate', 'method', 'status', 'reference',
            'bank_account', 'check_number', 'check_date',
            'card_last4', 'card_type', 'authorization_code',
            'transaction_id', 'payment_gateway', 'notes',
            'created_at', 'updated_at', 'created_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError(
                _("Payment amount must be greater than zero")
            )
        
        invoice = data['invoice']
        if data['amount'] > invoice.balance_due:
            raise serializers.ValidationError(
                _("Payment amount cannot exceed invoice balance")
            )
        
        if data['method'] == 'check' and not data.get('check_number'):
            raise serializers.ValidationError(
                _("Check number is required for check payments")
            )
        
        return data

class RecurringInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringInvoiceItem
        fields = (
            'id', 'recurring_invoice', 'description',
            'quantity', 'unit_price', 'discount_rate',
            'tax_rate', 'income_account', 'tax_account'
        )

    def validate(self, data):
        if data['quantity'] <= 0:
            raise serializers.ValidationError(
                _("Quantity must be greater than zero")
            )
        if data['unit_price'] < 0:
            raise serializers.ValidationError(
                _("Unit price cannot be negative")
            )
        return data

class RecurringInvoiceSerializer(serializers.ModelSerializer):
    items = RecurringInvoiceItemSerializer(many=True)
    next_invoice_date = serializers.DateField(source='next_date', read_only=True)
    
    class Meta:
        model = RecurringInvoice
        fields = (
            'id', 'organization', 'name', 'description',
            'start_date', 'end_date', 'frequency',
            'next_invoice_date', 'invoice_type',
            'party_name', 'party_tax_id', 'party_address',
            'party_email', 'party_phone', 'terms',
            'notes', 'is_active', 'auto_send',
            'days_due', 'items', 'created_at',
            'updated_at', 'created_by'
        )
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                _("End date must be after start date")
            )
        
        items = self.initial_data.get('items', [])
        if not items:
            raise serializers.ValidationError(
                _("At least one item is required")
            )
        
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        recurring_invoice = RecurringInvoice.objects.create(**validated_data)
        
        for item_data in items_data:
            RecurringInvoiceItem.objects.create(
                recurring_invoice=recurring_invoice,
                **item_data
            )
        
        return recurring_invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        
        # Update recurring invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle items
        instance.items.all().delete()
        for item_data in items_data:
            RecurringInvoiceItem.objects.create(
                recurring_invoice=instance,
                **item_data
            )
        
        return instance 