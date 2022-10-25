import json
import stripe

from .sofort_checkout import complete_sofort_checkout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .stripe_psp_data import update_sofort_failure_psp_data, update_refund_psp_data
from .utils import get_payment_object, is_sofort_payment, \
    has_matching_app_id


# NOTE: This does handle all stripe payments (not only sofort)
@csrf_exempt
def stripe_webhook(request):
    body = json.loads(request.body)

    try:
        event = stripe.Event.construct_from(body, stripe.api_key)
    except ValueError:
        return HttpResponse(status=400)

    return handle_sofort_webhook_event(request, event)


def handle_sofort_webhook_event(request, event):
    if event.type == "payment_intent.processing":
        handle_processing_payments(request, event)
    elif event.type == "payment_intent.payment_failed":
        handle_payment_failures(event)
    elif event.type == "charge.refunded":
        handle_refunds(event)

    return HttpResponse(status=200)


# Filter SOFORT and APP_ID and complete checkout for webhook processing
def handle_processing_payments(request, event):
    payment_intent = get_payment_object(event)

    if is_sofort_payment(payment_intent) and has_matching_app_id(payment_intent):
        complete_sofort_checkout(request, payment_intent)


# For CC and SOFORT => Update psp data
def handle_refunds(event):
    charge = get_payment_object(event)

    update_refund_psp_data(charge)


# Filter SOFORT only and update psp state
def handle_payment_failures(event):
    payment_intent = get_payment_object(event)

    if is_sofort_payment(payment_intent):
        update_sofort_failure_psp_data(payment_intent)
