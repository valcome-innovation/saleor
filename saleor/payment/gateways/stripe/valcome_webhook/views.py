import json
import stripe

from saleor.core.transactions import transaction_with_commit_on_errors
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .sofort_checkout import complete_stripe_checkout
from .stripe_psp_data import update_refund_psp_data, \
    update_failure_psp_data
from .utils import get_payment_object, \
    has_matching_app_id


# NOTE: This does handle all stripe payments
@csrf_exempt
@transaction_with_commit_on_errors()
def stripe_webhook(request):
    body = json.loads(request.body)

    try:
        event = stripe.Event.construct_from(body, stripe.api_key)
    except ValueError:
        return HttpResponse(status=400)

    return handle_webhook_event(request, event)


def handle_webhook_event(request, event):
    if event.type == "payment_intent.processing" \
            or event.type == "payment_intent.succeeded":
        handle_processing_payments(request, event)
    elif event.type == "payment_intent.payment_failed":
        handle_payment_failures(event)
    elif event.type == "charge.refunded":
        handle_refunds(event)

    return HttpResponse(status=200)


# Filter APP_ID and complete checkout for webhook processing
def handle_processing_payments(request, event):
    payment_intent = get_payment_object(event)

    if has_matching_app_id(payment_intent):
        complete_stripe_checkout(request, payment_intent)


# Update psp data
def handle_refunds(event):
    charge = get_payment_object(event)

    update_refund_psp_data(charge)


# Update psp state
def handle_payment_failures(event):
    payment_intent = get_payment_object(event)

    update_failure_psp_data(payment_intent)
