from ..graphql.checkout.mutations import CheckoutComplete
from ..graphql.payment.mutations import CheckoutPaymentCreate
from ..graphql.checkout.types import Checkout
from ..graphql.account.types import models
from graphql_relay import to_global_id


def handle_sofort(payment_intent, info):
    checkout_token = payment_intent.metadata.checkoutToken
    checkout_id = str(checkout_token)
    checkout_payment_create = CheckoutPaymentCreate()
    checkout_complete = CheckoutComplete()

    data = {
        "input": {
            "token": payment_intent.payment_method,
            "gateway": "mirumee.payments.stripe",
            "payment_intent": payment_intent.id
        }
    }

    global_checkout_id = to_global_id(Checkout._meta.name, checkout_id)
    print(global_checkout_id)

    payment = checkout_payment_create.create_payment_from_checkout(info, checkout_id, data)

    user_id = payment.checkout.user_id
    user = models.User.objects.get(pk=user_id)
    info.context.user = user

    checkout_complete.complete_checkout(info, global_checkout_id, False, data)
