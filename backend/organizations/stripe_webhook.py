import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from organizations.models import Organization, OrganizationMembership
from users.models import User

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Maneja los eventos relevantes
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                org.plan = 'pro'
                org.save()
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                status = subscription['status']
                if status == 'active':
                    org.plan = 'pro'
                else:
                    org.plan = 'free'
                org.save()
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                org.plan = 'free'
                org.save()
    elif event['type'] == 'invoice.paid':
        # TODO: Marca la suscripción como pagada
        pass
    elif event['type'] == 'invoice.payment_failed':
        # TODO: Notifica al usuario/sponsor
        pass
    elif event['type'] == 'checkout.session.completed':
        # TODO: Marca la suscripción como activa
        pass

    return HttpResponse(status=200) 