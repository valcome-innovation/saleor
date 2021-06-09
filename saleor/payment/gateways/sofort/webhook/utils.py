from ....models import Payment, Checkout as CheckoutModel
from .....graphql.checkout.mutations import CheckoutComplete
from .....graphql.payment.mutations import CheckoutPaymentCreate
from .....graphql.checkout.types import Checkout
from .....graphql.account.types import models
from graphql_relay import to_global_id


def handle_sofort(payment_intent, info):
    checkout_token = str(payment_intent.metadata.checkout_token)
    if not _is_checkout_processing(checkout_token):
        info.context.user = CheckoutModel.objects.get(pk=checkout_token).user
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
        CheckoutComplete().perform_mutation(None, info, global_checkout_id, False, **data)
    except Exception as e:
        _update_checkout_webhook_processing(checkout_token, False)
        raise e


def _create_payment_data(payment_intent):
    return {
        "payment_data": {
            "payment_intent": payment_intent
        }
    }

