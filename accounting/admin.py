from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Account, Transaction, TransactionEntry,
    Budget, BudgetItem, Invoice, InvoiceItem,
    FixedAsset, TaxRate, Payment,
    RecurringInvoice, RecurringInvoiceItem
)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'organization', 'account_type', 'subtype', 'current_balance', 'is_active')
    list_filter = ('organization', 'account_type', 'subtype', 'is_active', 'is_archived')
    search_fields = ('code', 'name', 'description')
    raw_id_fields = ('organization', 'parent', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'name', 'code', 'description')
        }),
        (_('Account Classification'), {
            'fields': ('account_type', 'subtype', 'parent')
        }),
        (_('Balance Information'), {
            'fields': ('current_balance', 'available_balance', 'currency')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_archived')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'organization', 'description', 'status', 'total_amount', 'created_by')
    list_filter = ('organization', 'status', 'is_recurring', 'date', 'created_at')
    search_fields = ('description', 'reference')
    raw_id_fields = ('organization', 'created_by', 'approved_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'approved_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'date', 'description', 'reference')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Recurrence'), {
            'fields': ('is_recurring', 'recurrence_type', 'recurrence_end_date'),
            'classes': ('collapse',)
        }),
        (_('Tags'), {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'approved_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        type('TransactionEntryInline', (admin.TabularInline,), {
            'model': TransactionEntry,
            'extra': 1,
            'raw_id_fields': ('account',),
        })
    ]

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'start_date', 'end_date', 'period', 'is_active')
    list_filter = ('organization', 'period', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    raw_id_fields = ('organization', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'name', 'description')
        }),
        (_('Period'), {
            'fields': ('start_date', 'end_date', 'period')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        type('BudgetItemInline', (admin.TabularInline,), {
            'model': BudgetItem,
            'extra': 1,
            'raw_id_fields': ('account',),
        })
    ]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'organization', 'type', 'party_name', 'date', 'due_date', 'total', 'status')
    list_filter = ('organization', 'type', 'status', 'date', 'created_at')
    search_fields = ('number', 'reference', 'party_name', 'party_tax_id')
    raw_id_fields = ('organization', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'subtotal', 'tax_amount', 'total', 'amount_paid')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'type', 'number', 'reference')
        }),
        (_('Dates'), {
            'fields': ('date', 'due_date')
        }),
        (_('Party Information'), {
            'fields': ('party_name', 'party_tax_id', 'party_address', 'party_email', 'party_phone')
        }),
        (_('Amounts'), {
            'fields': ('subtotal', 'tax_amount', 'total', 'amount_paid', 'currency', 'exchange_rate')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'terms'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        type('InvoiceItemInline', (admin.TabularInline,), {
            'model': InvoiceItem,
            'extra': 1,
            'raw_id_fields': ('income_account', 'tax_account'),
        })
    ]

@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_number', 'name', 'organization', 'purchase_date', 'purchase_cost', 'current_value', 'status')
    list_filter = ('organization', 'status', 'purchase_date', 'created_at')
    search_fields = ('asset_number', 'name', 'description')
    raw_id_fields = ('organization', 'custodian', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'name', 'description', 'asset_number')
        }),
        (_('Purchase Information'), {
            'fields': ('purchase_date', 'purchase_cost')
        }),
        (_('Depreciation'), {
            'fields': ('useful_life_years', 'salvage_value', 'depreciation_method',
                      'current_value', 'accumulated_depreciation')
        }),
        (_('Location & Tracking'), {
            'fields': ('location', 'custodian')
        }),
        (_('Insurance'), {
            'fields': ('insurance_policy', 'insurance_expiry'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'rate', 'is_compound', 'is_recoverable', 'is_active')
    list_filter = ('organization', 'is_compound', 'is_recoverable', 'is_active')
    search_fields = ('name', 'description')
    raw_id_fields = ('organization', 'sales_tax_account', 'purchase_tax_account')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'name', 'description', 'rate')
        }),
        (_('Configuration'), {
            'fields': ('is_compound', 'is_recoverable')
        }),
        (_('Account Mapping'), {
            'fields': ('sales_tax_account', 'purchase_tax_account')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'date', 'amount', 'method', 'status', 'reference')
    list_filter = ('organization', 'method', 'status', 'date', 'created_at')
    search_fields = ('reference', 'transaction_id', 'check_number')
    raw_id_fields = ('organization', 'invoice', 'bank_account', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'invoice', 'date', 'amount')
        }),
        (_('Payment Details'), {
            'fields': ('method', 'status', 'reference', 'bank_account')
        }),
        (_('Check Information'), {
            'fields': ('check_number', 'check_date'),
            'classes': ('collapse',)
        }),
        (_('Card Information'), {
            'fields': ('card_last4', 'card_type', 'authorization_code'),
            'classes': ('collapse',)
        }),
        (_('Online Payment'), {
            'fields': ('transaction_id', 'payment_gateway'),
            'classes': ('collapse',)
        }),
        (_('Currency'), {
            'fields': ('currency', 'exchange_rate')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'frequency', 'start_date', 'next_date', 'is_active')
    list_filter = ('organization', 'frequency', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'party_name')
    raw_id_fields = ('organization', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'name', 'description')
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date', 'frequency', 'next_date')
        }),
        (_('Template Data'), {
            'fields': ('invoice_type', 'party_name', 'party_tax_id', 'party_address',
                      'party_email', 'party_phone')
        }),
        (_('Additional Information'), {
            'fields': ('terms', 'notes'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('is_active', 'auto_send', 'days_due')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        type('RecurringInvoiceItemInline', (admin.TabularInline,), {
            'model': RecurringInvoiceItem,
            'extra': 1,
            'raw_id_fields': ('income_account', 'tax_account'),
        })
    ]
