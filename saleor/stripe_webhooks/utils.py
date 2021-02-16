from ..graphql.checkout.mutations import CheckoutComplete
from ..graphql.payment.mutations import CheckoutPaymentCreate
from ..graphql.checkout.types import Checkout as CheckoutType
from ..graphql.account.types import models
from ..checkout.models import Checkout as CheckoutModel
from graphql_relay import to_global_id


def handle_sofort(payment_intent, info):
    checkout_id = str(payment_intent.metadata.checkoutToken)

    if not is_checkout_processing(checkout_id):
        checkout_payment_create = CheckoutPaymentCreate()
        update_checkout_webhook_processing(checkout_id, True)
        payment_data = create_payment_data(payment_intent)
        payment = checkout_payment_create.create_payment_from_checkout(info, checkout_id, payment_data)
        info.context.user = get_user_from_payment(payment)
        complete_checkout(info, checkout_id, payment_data)


def is_checkout_processing(checkout_id):
    checkout = CheckoutModel.objects.only("webhook_processing").get(pk=checkout_id)
    return checkout.webhook_processing


def update_checkout_webhook_processing(checkout_id, processing):
    CheckoutModel.objects.filter(pk=checkout_id).update(webhook_processing=processing)


def create_payment_data(payment_intent):
    return {
        "input": {
            "token": payment_intent.payment_method,
            "gateway": "mirumee.payments.stripe",
            "payment_intent": payment_intent.id
        }
    }


def get_user_from_payment(payment):
    user_id = payment.checkout.user_id
    return models.User.objects.get(pk=user_id)


def complete_checkout(info, checkout_id, data):
    try:
        global_checkout_id = to_global_id(CheckoutType._meta.name, checkout_id)
        CheckoutComplete().complete_checkout(info, global_checkout_id, False, data)
    except Exception as e:
        update_checkout_webhook_processing(checkout_id, False)
        raise e
