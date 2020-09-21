import json
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def stripe_webhook(request):
    print(request)
    payload = request.body
    event = None

    print("test")
    print(request)

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        print("success")
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        # Then define and call a method to handle the successful payment intent.
        # handle_payment_intent_succeeded(payment_intent)
    elif event.type == 'payment_method.attached':
        payment_method = event.data.object  # contains a stripe.PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
    # ... handle other event types
    else:
        # Unexpected event type
        return HttpResponse(status=400)

    return HttpResponse(status=200)
