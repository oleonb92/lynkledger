from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'fixed-assets', views.FixedAssetViewSet, basename='fixed-asset')
router.register(r'tax-rates', views.TaxRateViewSet, basename='tax-rate')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'recurring-invoices', views.RecurringInvoiceViewSet, basename='recurring-invoice')

# Additional views for reports and specific functionality
report_patterns = [
    # Balance Sheet
    path(
        'reports/balance-sheet/',
        views.BalanceSheetView.as_view(),
        name='balance-sheet'
    ),
    # Income Statement
    path(
        'reports/income-statement/',
        views.IncomeStatementView.as_view(),
        name='income-statement'
    ),
    # Cash Flow Statement
    path(
        'reports/cash-flow/',
        views.CashFlowStatementView.as_view(),
        name='cash-flow-statement'
    ),
    # Trial Balance
    path(
        'reports/trial-balance/',
        views.TrialBalanceView.as_view(),
        name='trial-balance'
    ),
    # Aged Receivables
    path(
        'reports/aged-receivables/',
        views.AgedReceivablesView.as_view(),
        name='aged-receivables'
    ),
    # Aged Payables
    path(
        'reports/aged-payables/',
        views.AgedPayablesView.as_view(),
        name='aged-payables'
    ),
    # Budget vs Actual
    path(
        'reports/budget-vs-actual/',
        views.BudgetVsActualView.as_view(),
        name='budget-vs-actual'
    ),
    # Tax Summary
    path(
        'reports/tax-summary/',
        views.TaxSummaryView.as_view(),
        name='tax-summary'
    ),
]

# Additional functionality patterns
functionality_patterns = [
    # Account reconciliation
    path(
        'accounts/<int:pk>/reconcile/',
        views.AccountReconciliationView.as_view(),
        name='account-reconciliation'
    ),
    # Bulk transaction import
    path(
        'transactions/import/',
        views.TransactionImportView.as_view(),
        name='transaction-import'
    ),
    # Bulk transaction export
    path(
        'transactions/export/',
        views.TransactionExportView.as_view(),
        name='transaction-export'
    ),
    # Generate recurring invoices
    path(
        'recurring-invoices/generate-all/',
        views.GenerateRecurringInvoicesView.as_view(),
        name='generate-recurring-invoices'
    ),
    # Generate financial statements
    path(
        'reports/generate/',
        views.GenerateFinancialStatementsView.as_view(),
        name='generate-financial-statements'
    ),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(report_patterns)),
    path('', include(functionality_patterns)),
] 