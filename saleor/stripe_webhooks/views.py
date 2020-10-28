import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import handle_sofort

class Info:
  def __init__(self, context):
    self.context = context


@csrf_exempt
def stripe_webhook(request):
    payload = request.body

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        payment_intent = event.data.object
    except ValueError as e:
        return HttpResponse(status=400)

    if hasattr(payment_intent.metadata, 'appId') \
            and payment_intent.metadata.appId != settings.APP_ID:
        return HttpResponse(status=200)  # skip webhook on not relevant apps

    if hasattr(payment_intent, "payment_method_types") \
            and "sofort" in payment_intent.payment_method_types:
        if event.type == 'payment_intent.processing':
                info = Info(request)
                handle_sofort(payment_intent, info)
        elif event.type == 'payment_intent.failed':
                return HttpResponse(status=400)

    return HttpResponse(status=200)
