from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'budgets', views.BudgetViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'fixed-assets', views.FixedAssetViewSet)
router.register(r'tax-rates', views.TaxRateViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'recurring-invoices', views.RecurringInvoiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 