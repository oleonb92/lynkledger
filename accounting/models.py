from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from organizations.models import Organization
from decimal import Decimal
from datetime import timedelta

class Account(models.Model):
    class AccountType(models.TextChoices):
        ASSET = 'asset', _('Asset')
        LIABILITY = 'liability', _('Liability')
        EQUITY = 'equity', _('Equity')
        INCOME = 'income', _('Income')
        EXPENSE = 'expense', _('Expense')

    class AccountSubType(models.TextChoices):
        # Asset subtypes
        CASH = 'cash', _('Cash')
        BANK = 'bank', _('Bank Account')
        RECEIVABLE = 'receivable', _('Accounts Receivable')
        INVENTORY = 'inventory', _('Inventory')
        FIXED_ASSET = 'fixed_asset', _('Fixed Asset')
        
        # Liability subtypes
        PAYABLE = 'payable', _('Accounts Payable')
        CREDIT_CARD = 'credit_card', _('Credit Card')
        LOAN = 'loan', _('Loan')
        
        # Income subtypes
        SALES = 'sales', _('Sales')
        SERVICE = 'service', _('Service Revenue')
        INTEREST = 'interest', _('Interest Income')
        
        # Expense subtypes
        COST_OF_GOODS = 'cost_of_goods', _('Cost of Goods Sold')
        OPERATING = 'operating', _('Operating Expense')
        PAYROLL = 'payroll', _('Payroll')
        TAX = 'tax', _('Tax')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=255)
    code = models.CharField(_('code'), max_length=20, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    account_type = models.CharField(
        _('account type'),
        max_length=20,
        choices=AccountType.choices
    )
    subtype = models.CharField(
        _('account subtype'),
        max_length=20,
        choices=AccountSubType.choices,
        blank=True
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent account')
    )
    
    # Balance tracking
    current_balance = models.DecimalField(
        _('current balance'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    available_balance = models.DecimalField(
        _('available balance'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Settings
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    is_active = models.BooleanField(_('active'), default=True)
    is_archived = models.BooleanField(_('archived'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_accounts',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        unique_together = ('organization', 'code')
        ordering = ['code', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name

    def update_balance(self, amount):
        """Update account balance with double-entry validation."""
        self.current_balance += amount
        self.save(update_fields=['current_balance', 'updated_at'])

class Transaction(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Approval')
        APPROVED = 'approved', _('Approved')
        POSTED = 'posted', _('Posted')
        RECONCILED = 'reconciled', _('Reconciled')
        VOID = 'void', _('Void')

    class RecurrenceType(models.TextChoices):
        NONE = 'none', _('None')
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        YEARLY = 'yearly', _('Yearly')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('organization')
    )
    date = models.DateField(_('date'))
    description = models.TextField(_('description'))
    reference = models.CharField(_('reference'), max_length=50, blank=True)
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Recurrence
    is_recurring = models.BooleanField(_('is recurring'), default=False)
    recurrence_type = models.CharField(
        _('recurrence type'),
        max_length=20,
        choices=RecurrenceType.choices,
        default=RecurrenceType.NONE
    )
    recurrence_end_date = models.DateField(_('recurrence end date'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transactions',
        verbose_name=_('created by')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transactions',
        verbose_name=_('approved by')
    )
    
    # Tags for categorization
    tags = models.JSONField(_('tags'), default=list, blank=True)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} - {self.description[:50]}"

    @property
    def total_amount(self):
        return sum(entry.amount for entry in self.entries.all())

    def is_balanced(self):
        """Check if the transaction is balanced (debits = credits)"""
        return abs(self.total_amount) < 0.01

class TransactionEntry(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=_('transaction')
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name=_('account')
    )
    description = models.CharField(_('description'), max_length=255, blank=True)
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    
    # Optional fields for better tracking
    tax_rate = models.DecimalField(
        _('tax rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    exchange_rate = models.DecimalField(
        _('exchange rate'),
        max_digits=10,
        decimal_places=6,
        default=1,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _('transaction entry')
        verbose_name_plural = _('transaction entries')

    def __str__(self):
        return f"{self.account} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.account.update_balance(self.amount)

class Budget(models.Model):
    class Period(models.TextChoices):
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        YEARLY = 'yearly', _('Yearly')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    period = models.CharField(
        _('period'),
        max_length=20,
        choices=Period.choices,
        default=Period.MONTHLY
    )
    
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_budgets',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('budget')
        verbose_name_plural = _('budgets')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class BudgetItem(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('budget')
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='budget_items',
        verbose_name=_('account')
    )
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    
    # For flexible budgeting
    minimum_amount = models.DecimalField(
        _('minimum amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    maximum_amount = models.DecimalField(
        _('maximum amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        verbose_name = _('budget item')
        verbose_name_plural = _('budget items')
        unique_together = ('budget', 'account')

    def __str__(self):
        return f"{self.budget.name} - {self.account.name}"

    @property
    def actual_amount(self):
        """Calculate actual amount spent/earned for this budget item"""
        # Implementation depends on your specific requirements
        pass

    @property
    def variance(self):
        """Calculate variance between budgeted and actual amounts"""
        actual = self.actual_amount
        if actual is not None:
            return self.amount - actual
        return None

class Invoice(models.Model):
    class Type(models.TextChoices):
        SALE = 'sale', _('Sales Invoice')
        PURCHASE = 'purchase', _('Purchase Invoice')
        CREDIT_NOTE = 'credit_note', _('Credit Note')
        DEBIT_NOTE = 'debit_note', _('Debit Note')

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SENT = 'sent', _('Sent')
        APPROVED = 'approved', _('Approved')
        PAID = 'paid', _('Paid')
        PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
        OVERDUE = 'overdue', _('Overdue')
        VOID = 'void', _('Void')
        CANCELLED = 'cancelled', _('Cancelled')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('organization')
    )
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=Type.choices,
        default=Type.SALE
    )
    number = models.CharField(_('number'), max_length=50)
    reference = models.CharField(_('reference'), max_length=50, blank=True)
    
    # Dates
    date = models.DateField(_('date'))
    due_date = models.DateField(_('due date'))
    
    # Party information
    party_name = models.CharField(_('party name'), max_length=255)
    party_tax_id = models.CharField(_('party tax ID'), max_length=50, blank=True)
    party_address = models.TextField(_('party address'), blank=True)
    party_email = models.EmailField(_('party email'), blank=True)
    party_phone = models.CharField(_('party phone'), max_length=50, blank=True)
    
    # Amounts
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        _('total'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    amount_paid = models.DecimalField(
        _('amount paid'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Additional fields
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    exchange_rate = models.DecimalField(
        _('exchange rate'),
        max_digits=10,
        decimal_places=6,
        default=1
    )
    notes = models.TextField(_('notes'), blank=True)
    terms = models.TextField(_('terms'), blank=True)
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        unique_together = ('organization', 'number')
        ordering = ['-date', '-number']

    def __str__(self):
        return f"{self.number} - {self.party_name}"

    def calculate_totals(self):
        """Calculate invoice totals from items"""
        self.subtotal = sum(item.amount for item in self.items.all())
        self.tax_amount = sum(item.tax_amount for item in self.items.all())
        self.total = self.subtotal + self.tax_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total'])

    @property
    def balance_due(self):
        return self.total - self.amount_paid

    @property
    def is_paid(self):
        return self.amount_paid >= self.total

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('invoice')
    )
    description = models.CharField(_('description'), max_length=255)
    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_rate = models.DecimalField(
        _('discount rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    tax_rate = models.DecimalField(
        _('tax rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Account mapping
    income_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoice_income_items',
        verbose_name=_('income account')
    )
    tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='invoice_tax_items',
        verbose_name=_('tax account')
    )

    class Meta:
        verbose_name = _('invoice item')
        verbose_name_plural = _('invoice items')

    def __str__(self):
        return f"{self.invoice.number} - {self.description}"

    @property
    def amount(self):
        """Calculate net amount after discount"""
        gross = self.quantity * self.unit_price
        discount = gross * (self.discount_rate / Decimal('100'))
        return gross - discount

    @property
    def tax_amount(self):
        """Calculate tax amount"""
        return self.amount * (self.tax_rate / Decimal('100'))

class FixedAsset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        DISPOSED = 'disposed', _('Disposed')
        SOLD = 'sold', _('Sold')
        WRITTEN_OFF = 'written_off', _('Written Off')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='fixed_assets',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    asset_number = models.CharField(_('asset number'), max_length=50, unique=True)
    
    purchase_date = models.DateField(_('purchase date'))
    purchase_cost = models.DecimalField(
        _('purchase cost'),
        max_digits=15,
        decimal_places=2
    )
    
    # Depreciation settings
    useful_life_years = models.PositiveIntegerField(_('useful life (years)'))
    salvage_value = models.DecimalField(
        _('salvage value'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    depreciation_method = models.CharField(
        _('depreciation method'),
        max_length=20,
        choices=[
            ('straight_line', _('Straight Line')),
            ('declining_balance', _('Declining Balance')),
            ('sum_of_years', _('Sum of Years Digits'))
        ],
        default='straight_line'
    )
    
    # Current status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    current_value = models.DecimalField(
        _('current value'),
        max_digits=15,
        decimal_places=2
    )
    accumulated_depreciation = models.DecimalField(
        _('accumulated depreciation'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Location and tracking
    location = models.CharField(_('location'), max_length=255, blank=True)
    custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        verbose_name=_('custodian')
    )
    
    # Insurance
    insurance_policy = models.CharField(_('insurance policy'), max_length=50, blank=True)
    insurance_expiry = models.DateField(_('insurance expiry'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('fixed asset')
        verbose_name_plural = _('fixed assets')
        ordering = ['asset_number']

    def __str__(self):
        return f"{self.asset_number} - {self.name}"

    def calculate_depreciation(self, date):
        """Calculate depreciation amount up to the given date"""
        if self.status != self.Status.ACTIVE:
            return 0
            
        years_held = (date - self.purchase_date).days / 365.25
        if years_held > self.useful_life_years:
            years_held = self.useful_life_years
            
        depreciable_amount = self.purchase_cost - self.salvage_value
        
        if self.depreciation_method == 'straight_line':
            return (depreciable_amount / self.useful_life_years) * years_held
        elif self.depreciation_method == 'declining_balance':
            rate = 2 / self.useful_life_years  # Double declining balance
            return depreciable_amount * (1 - (1 - rate) ** years_held)
        else:  # Sum of years digits
            sum_of_years = (self.useful_life_years * (self.useful_life_years + 1)) / 2
            remaining_life = self.useful_life_years - years_held
            return depreciable_amount * (remaining_life / sum_of_years)

class TaxRate(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='tax_rates',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    rate = models.DecimalField(
        _('rate'),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Tax configuration
    is_compound = models.BooleanField(_('compound tax'), default=False)
    is_recoverable = models.BooleanField(_('recoverable'), default=True)
    
    # Account mapping
    sales_tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='sales_tax_rates',
        verbose_name=_('sales tax account')
    )
    purchase_tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='purchase_tax_rates',
        verbose_name=_('purchase tax account')
    )
    
    # Metadata
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('tax rate')
        verbose_name_plural = _('tax rates')
        unique_together = ('organization', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        CHECK = 'check', _('Check')
        CREDIT_CARD = 'credit_card', _('Credit Card')
        DEBIT_CARD = 'debit_card', _('Debit Card')
        ONLINE = 'online', _('Online Payment')
        OTHER = 'other', _('Other')

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        VOIDED = 'voided', _('Voided')
        REFUNDED = 'refunded', _('Refunded')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('organization')
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('invoice')
    )
    
    date = models.DateField(_('date'))
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='USD')
    exchange_rate = models.DecimalField(
        _('exchange rate'),
        max_digits=10,
        decimal_places=6,
        default=1
    )
    
    method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=Method.choices
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Payment details
    reference = models.CharField(_('reference'), max_length=100, blank=True)
    bank_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('bank account')
    )
    
    # For check payments
    check_number = models.CharField(_('check number'), max_length=50, blank=True)
    check_date = models.DateField(_('check date'), null=True, blank=True)
    
    # For card payments
    card_last4 = models.CharField(_('card last 4 digits'), max_length=4, blank=True)
    card_type = models.CharField(_('card type'), max_length=20, blank=True)
    authorization_code = models.CharField(_('authorization code'), max_length=50, blank=True)
    
    # For online payments
    transaction_id = models.CharField(_('transaction ID'), max_length=100, blank=True)
    payment_gateway = models.CharField(_('payment gateway'), max_length=50, blank=True)
    
    notes = models.TextField(_('notes'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Payment {self.id} - {self.invoice.number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == self.Status.COMPLETED:
            # Update invoice paid amount
            self.invoice.amount_paid = sum(
                payment.amount 
                for payment in self.invoice.payments.filter(
                    status=self.Status.COMPLETED
                )
            )
            self.invoice.save(update_fields=['amount_paid'])

class RecurringInvoice(models.Model):
    class Frequency(models.TextChoices):
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        YEARLY = 'yearly', _('Yearly')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='recurring_invoices',
        verbose_name=_('organization')
    )
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Schedule
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), null=True, blank=True)
    frequency = models.CharField(
        _('frequency'),
        max_length=20,
        choices=Frequency.choices
    )
    next_date = models.DateField(_('next date'))
    
    # Template data
    invoice_type = models.CharField(
        _('invoice type'),
        max_length=20,
        choices=Invoice.Type.choices,
        default=Invoice.Type.SALE
    )
    party_name = models.CharField(_('party name'), max_length=255)
    party_tax_id = models.CharField(_('party tax ID'), max_length=50, blank=True)
    party_address = models.TextField(_('party address'), blank=True)
    party_email = models.EmailField(_('party email'), blank=True)
    party_phone = models.CharField(_('party phone'), max_length=50, blank=True)
    
    terms = models.TextField(_('terms'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Settings
    is_active = models.BooleanField(_('active'), default=True)
    auto_send = models.BooleanField(_('auto send'), default=False)
    days_due = models.PositiveIntegerField(_('days due'), default=30)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_recurring_invoices',
        verbose_name=_('created by')
    )

    class Meta:
        verbose_name = _('recurring invoice')
        verbose_name_plural = _('recurring invoices')
        ordering = ['name']

    def __str__(self):
        return self.name

    def generate_invoice(self):
        """Generate a new invoice from this template"""
        invoice = Invoice.objects.create(
            organization=self.organization,
            type=self.invoice_type,
            date=self.next_date,
            due_date=self.next_date + timedelta(days=self.days_due),
            party_name=self.party_name,
            party_tax_id=self.party_tax_id,
            party_address=self.party_address,
            party_email=self.party_email,
            party_phone=self.party_phone,
            terms=self.terms,
            notes=self.notes,
            created_by=self.created_by
        )
        
        # Copy items from template
        for template_item in self.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                description=template_item.description,
                quantity=template_item.quantity,
                unit_price=template_item.unit_price,
                discount_rate=template_item.discount_rate,
                tax_rate=template_item.tax_rate,
                income_account=template_item.income_account,
                tax_account=template_item.tax_account
            )
        
        invoice.calculate_totals()
        return invoice

    def update_next_date(self):
        """Update the next generation date based on frequency"""
        if not self.is_active or (self.end_date and self.next_date >= self.end_date):
            return
            
        if self.frequency == self.Frequency.DAILY:
            self.next_date += timedelta(days=1)
        elif self.frequency == self.Frequency.WEEKLY:
            self.next_date += timedelta(weeks=1)
        elif self.frequency == self.Frequency.MONTHLY:
            # Add one month, handling month end dates
            year = self.next_date.year + (self.next_date.month // 12)
            month = (self.next_date.month % 12) + 1
            day = min(self.next_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            self.next_date = self.next_date.replace(year=year, month=month, day=day)
        elif self.frequency == self.Frequency.QUARTERLY:
            # Add three months
            year = self.next_date.year + ((self.next_date.month + 2) // 12)
            month = ((self.next_date.month + 2) % 12) + 1
            day = min(self.next_date.day, [31,29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
            self.next_date = self.next_date.replace(year=year, month=month, day=day)
        else:  # YEARLY
            self.next_date = self.next_date.replace(year=self.next_date.year + 1)
        
        self.save(update_fields=['next_date'])

class RecurringInvoiceItem(models.Model):
    recurring_invoice = models.ForeignKey(
        RecurringInvoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('recurring invoice')
    )
    description = models.CharField(_('description'), max_length=255)
    quantity = models.DecimalField(
        _('quantity'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_rate = models.DecimalField(
        _('discount rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    tax_rate = models.DecimalField(
        _('tax rate'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Account mapping
    income_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_items',
        verbose_name=_('income account')
    )
    tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='recurring_invoice_tax_items',
        verbose_name=_('tax account')
    )

    class Meta:
        verbose_name = _('recurring invoice item')
        verbose_name_plural = _('recurring invoice items')

    def __str__(self):
        return f"{self.recurring_invoice.name} - {self.description}"
