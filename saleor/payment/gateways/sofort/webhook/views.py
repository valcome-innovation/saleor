import json
import stripe

from ..... import settings
from .....graphql.api import schema
from .....streaming import stream_settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import handle_sofort


class Info:
    def __init__(self, context, schema):
        self.context = context
        self.schema = schema


@csrf_exempt
def stripe_webhook(request):
    try:
        event_type, payment_intent = get_event_type_and_payment_intent(request)
    except ValueError:
        return HttpResponse(status=400)

    return handle_stripe_webhook_event(request, event_type, payment_intent)


def get_event_type_and_payment_intent(request):
    request_body_json = json.loads(request.body)
    event = stripe.Event.construct_from(request_body_json, stripe.api_key)
    return event.type, event.data.object


def handle_stripe_webhook_event(request, event_type, payment_intent):
    if has_matching_app_id(payment_intent) and has_sofort_payment_method(payment_intent):
        return process_sofort_webhook_event(request, event_type, payment_intent)
    else:
        return HttpResponse(status=200)  # skip webhooks not meant for this app


# Verify if stripe request comes from same app (skipped for local development)
def has_matching_app_id(payment_intent):
    return not hasattr(payment_intent.metadata, "app_id") \
           or payment_intent.metadata.app_id == stream_settings.APP_ID \
           or settings.DEBUG


def has_sofort_payment_method(payment_intent):
    return hasattr(payment_intent, "payment_method_types") \
            and "sofort" in payment_intent.payment_method_types


def process_sofort_webhook_event(request, event_type, payment_intent):
    if event_type == "payment_intent.processing":
        info = Info(request, schema)
        handle_sofort(payment_intent, info)
        return HttpResponse(status=200)
    elif event_type == "payment_intent.failed":
        return HttpResponse(status=400)
    else:
        return HttpResponse(status=200)
