from django.core.handlers.asgi import ASGIRequest
from graphql_relay import to_global_id
from stripe.api_resources.payment_intent import PaymentIntent

from .utils import get_payment
from ....models import Checkout as CheckoutModel
from .....graphql.checkout.mutations import CheckoutComplete
from .....graphql.checkout.types import Checkout
from .....graphql.api import schema


class Info:
    def __init__(self, context, schema):
        self.context = context
        self.schema = schema


def complete_stripe_checkout(request: ASGIRequest,
                             payment_intent: PaymentIntent):
    info = Info(request, schema)
    payment = get_payment(payment_intent.id)

    # if payment doesn't exist, do nothing
    if not payment:
        return

    # order already created, nothing left to do
    if payment.order_id:
        return

    if payment.checkout:
        checkout = payment.checkout
        checkout_token = checkout.token

        if not checkout.webhook_processing:
            # Manually fill request context
            info.context.user = checkout.user
            info.context.app = None

            _update_checkout_webhook_processing(checkout_token, True)
            _complete_checkout(info, checkout_token, payment_intent)


def _is_checkout_processing(checkout_token):
    checkout = CheckoutModel.objects.only("webhook_processing").get(pk=checkout_token)
    return checkout.webhook_processing


def _update_checkout_webhook_processing(checkout_token, processing):
    CheckoutModel.objects.filter(pk=checkout_token).update(webhook_processing=processing)


def _complete_checkout(info, checkout_token, payment_intent):
    try:
        data = _create_payment_data(payment_intent)
        global_checkout_id = to_global_id(Checkout._meta.name, checkout_token)

        # Manually call graphql checkoutComplete request (always verify params)
        CheckoutComplete().perform_mutation(None, info, False, global_checkout_id, None, **data)
    except Exception as e:
        _update_checkout_webhook_processing(checkout_token, False)
        raise e


# Creates merged payment data for checkout complete and confirm payment
def _create_payment_data(payment_intent):
    return {
        "payment_data": {
            "payment_intent": payment_intent,
            **payment_intent.metadata
        }
    }
