from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet,
    OrganizationMembershipViewSet,
    OrganizationInvitationViewSet
)
from .stripe_webhook import stripe_webhook

app_name = 'organizations'

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'memberships', OrganizationMembershipViewSet, basename='membership')
router.register(r'invitations', OrganizationInvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
] 