import stripe

from ... import TransactionKind
from ....payment.gateways.stripe import get_amount_for_stripe
from ....payment.interface import (
    GatewayConfig,
    PaymentData,
    GatewayResponse,
    PaymentMethodInfo
)


def confirm_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    intent = payment_information.data.get("payment_intent", {})
    captured_amount = sum([charge.amount_captured for charge in intent.charges.data])
    is_fully_captured = intent.amount == captured_amount

    return GatewayResponse(
        is_success=is_fully_captured,
        kind=TransactionKind.CONFIRM,
        action_required=False,
        action_required_data=None,
        transaction_id=intent.id,
        amount=payment_information.amount,
        currency=payment_information.currency,
        raw_response=intent,
        customer_id=payment_information.customer_id,
        payment_method_info=PaymentMethodInfo(type="sofort"),
        error=None
    )


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    currency = payment_information.currency
    amount = payment_information.amount
    meta = payment_information.data.get("paymentMeta", {})

    intent = create_sofort_payment_intent(
        config=config,
        amount=payment_information.amount,
        currency=payment_information.currency,
        meta={
            "checkout_token": meta.get("checkoutToken", None),
            "checkout_params": meta.get("checkoutParams", None),
            "redirect_id": meta.get("redirectId", None)
        }
    )

    action_required_data = {"clientSecret": intent.client_secret}

    return GatewayResponse(
        is_success=True,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        amount=amount,
        currency=currency,
        transaction_id=intent.id,
        raw_response=intent,
        action_required=True,
        action_required_data=action_required_data,
        customer_id=payment_information.customer_id,
        payment_method_info=PaymentMethodInfo(type="sofort"),
        error=None
    )


def _get_client(**connection_params):
    stripe.api_key = connection_params.get("private_key")
    return stripe


def get_payment_meta(config: GatewayConfig, payment_intent_id):
    client = _get_client(**config.connection_params)
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id, client.api_key)
    return payment_intent.metadata


def create_sofort_payment_intent(config: GatewayConfig, amount, currency, meta):
    client = _get_client(**config.connection_params)
    cents = get_amount_for_stripe(amount, currency)

    return client.PaymentIntent.create(
        payment_method_types=['sofort'],
        amount=cents,
        currency=currency,
        confirmation_method='automatic',
        capture_method='automatic',
        metadata={
            "checkout_token": meta["checkout_token"],
            "checkout_params": meta["checkout_params"],
            "redirect_id": meta["redirect_id"]
        }
    )
