import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from organizations.models import Organization, OrganizationMembership, Incentive
from users.models import User
from django.utils import timezone
from django.core.mail import send_mail
from notifications.utils import send_plan_change_email, send_incentive_granted_email

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

    def create_incentive_if_applicable(org):
        # Si el sponsor es accountant y hay un cliente, crea incentivo
        if org.sponsor and org.sponsor_type == 'accountant':
            incentive, created = Incentive.objects.get_or_create(
                user=org.sponsor,
                organization=org,
                type='generic',  # Se puede ajustar luego
                defaults={
                    'status': 'pending',
                    'created_at': timezone.now()
                }
            )
            # Si quieres notificar al contador cuando se le otorga un incentivo, descomenta:
            # if created:
            #     send_incentive_granted_email(org.sponsor, org, incentive)

    def notify_plan_change(org, old_plan, new_plan):
        # Notifica a sponsor y owner usando el template HTML profesional
        if org.sponsor and org.sponsor.email:
            send_plan_change_email(org.sponsor, org, old_plan, new_plan)
        if org.owner and org.owner.email and org.owner.email != org.sponsor.email:
            send_plan_change_email(org.owner, org, old_plan, new_plan)
        # Hook para otras integraciones (ej: logs, Slack, etc.)
        # log_event('plan_change', org=org, old_plan=old_plan, new_plan=new_plan)

    # Maneja los eventos relevantes
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                old_plan = org.plan
                org.plan = 'pro'
                org.save()
                create_incentive_if_applicable(org)
                notify_plan_change(org, old_plan, 'pro')
                # Si el sponsor cambió, aquí puedes transferir la suscripción en Stripe
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                old_plan = org.plan
                status = subscription['status']
                if status == 'active':
                    org.plan = 'pro'
                    create_incentive_if_applicable(org)
                else:
                    org.plan = 'free'
                org.save()
                if old_plan != org.plan:
                    notify_plan_change(org, old_plan, org.plan)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        org_id = subscription['metadata'].get('org_id')
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org:
                old_plan = org.plan
                org.plan = 'free'
                org.save()
                if old_plan != 'free':
                    notify_plan_change(org, old_plan, 'free')
                # Si el sponsor era accountant y se elimina, notificar al owner para que asuma el pago
                if org.sponsor_type == 'accountant':
                    org.sponsor = org.owner
                    org.sponsor_type = 'client'
                    org.save()
                    # (Opcional) Notificar al owner
    elif event['type'] == 'organization.sponsor_changed':
        # Evento personalizado para cambio de sponsor
        org_id = event['data']['object'].get('org_id')
        new_sponsor_id = event['data']['object'].get('new_sponsor_id')
        sponsor_type = event['data']['object'].get('sponsor_type', 'client')
        org = Organization.objects.filter(id=org_id).first()
        if org and new_sponsor_id:
            new_sponsor = User.objects.filter(id=new_sponsor_id).first()
            if new_sponsor:
                org.transfer_sponsorship(new_sponsor, sponsor_type)
                # (Opcional) Transferir la suscripción en Stripe
                # (Opcional) Notificar al nuevo sponsor
    elif event['type'] == 'invoice.paid':
        # TODO: Marca la suscripción como pagada
        pass
    elif event['type'] == 'invoice.payment_failed':
        # Notifica al sponsor que el pago falló
        org_id = event['data']['object']['lines']['data'][0]['metadata'].get('org_id') if event['data']['object']['lines']['data'] else None
        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if org and org.sponsor and org.sponsor.email:
                send_mail(
                    f"Pago fallido en LynkLedger para '{org.name}'",
                    f"Hola,\n\nEl pago de la suscripción de la organización '{org.name}' ha fallado. Por favor, actualiza tu método de pago para evitar la interrupción del servicio.",
                    None,
                    [org.sponsor.email],
                    fail_silently=True
                )
    elif event['type'] == 'checkout.session.completed':
        # TODO: Marca la suscripción como activa
        pass
    # Hook para detectar cambios de sponsor (esto normalmente es manual, pero puedes dejarlo listo)
    # if event['type'] == 'organization.sponsor_changed':
    #     org_id = event['data']['object'].get('org_id')
    #     ...
    return HttpResponse(status=200) 