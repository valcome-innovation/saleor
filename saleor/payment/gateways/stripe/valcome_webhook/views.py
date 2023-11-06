import json

import sentry_sdk
import stripe
from django.core.handlers.asgi import ASGIRequest
from stripe.api_resources.charge import Charge
from stripe.api_resources.payment_intent import PaymentIntent

from saleor.core.transactions import transaction_with_commit_on_errors
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .stripe_checkout import complete_stripe_checkout
from .stripe_event import StripeEvent
from .stripe_psp_data import update_refund_psp_data, \
    update_failure_psp_data
from .utils import has_matching_app_id


# NOTE: This does handle all stripe payments
@csrf_exempt
@transaction_with_commit_on_errors()
def stripe_webhook(request: ASGIRequest):
    # Log 2
    try:
        sentry_sdk.capture_message("Stripe webhook initiated",
                                   level="info")
    except Exception as sentry_error:
        print(f"Sentry logging failed: {sentry_error}")

    body = json.loads(request.body)

    # Log 2
    try:
        event_id = body.get('id')
        print(f"Stripe webhook received - Event ID: {event_id}")
        sentry_sdk.capture_message(f"Stripe webhook received - Event ID: {event_id}",
                                   level="info")
    except Exception as sentry_error:
        print(f"Sentry logging failed: {sentry_error}")

    try:
        event: StripeEvent = stripe.Event.construct_from(body, stripe.api_key)
    except ValueError:
        return HttpResponse(status=400)

    return handle_webhook_event(request, event)


def handle_webhook_event(request: ASGIRequest, event: StripeEvent):
    data = event.data.object

    if event.type == "payment_intent.processing" \
            or event.type == "payment_intent.succeeded":
        handle_processing_payments(request, data)
    elif event.type == "payment_intent.payment_failed":
        handle_payment_failures(data)
    elif event.type == "charge.refunded":
        handle_refunds(data)

    return HttpResponse(status=200)


# Filter APP_ID and complete checkout for webhook processing
def handle_processing_payments(request: ASGIRequest,
                               payment_intent: PaymentIntent):
    if has_matching_app_id(payment_intent):
        complete_stripe_checkout(request, payment_intent)


# Update psp data
def handle_refunds(charge: Charge):
    update_refund_psp_data(charge)


# Update psp state
def handle_payment_failures(payment_intent: PaymentIntent):
    update_failure_psp_data(payment_intent)
