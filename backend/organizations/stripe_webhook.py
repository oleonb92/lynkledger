import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

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
        # TODO: Actualiza el modelo Organization/plan
        pass
    elif event['type'] == 'customer.subscription.updated':
        # TODO: Actualiza el modelo Organization/plan
        pass
    elif event['type'] == 'customer.subscription.deleted':
        # TODO: Suspende o baja de plan la organización
        pass
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