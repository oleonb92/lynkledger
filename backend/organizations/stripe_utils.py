import stripe
from django.conf import settings
from organizations.models import Organization

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_customer(user):
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
        )
        user.stripe_customer_id = customer['id']
        user.save()
    return user.stripe_customer_id


def create_stripe_subscription(user, plan_id):
    customer_id = create_stripe_customer(user)
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": plan_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
    )
    return subscription


def update_organization_plan(org: Organization, plan: str):
    org.plan = plan
    org.save()
    # Aquí puedes agregar lógica extra para activar features, etc. 