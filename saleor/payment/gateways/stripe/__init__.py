import stripe

from .consts import (
    STRIPE_API_VERSION,
)


def get_payment_meta(api_key, payment_intent_id):
    payment_intent = stripe.PaymentIntent.retrieve(
        payment_intent_id,
        api_key=api_key,
        stripe_version=STRIPE_API_VERSION,
    )
    return payment_intent.metadata
