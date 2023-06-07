import json

from saleor.payment.gateways.stripe.plugin import StripeGatewayPlugin
from saleor.plugins import manager


def resolve_payment_meta(payment_intent_id):
    stripe_plugin = manager.get_plugins_manager().get_plugin("saleor.payments.stripe")

    if isinstance(stripe_plugin, StripeGatewayPlugin):
        meta = stripe_plugin.get_payment_meta(payment_intent_id)

        return json.dumps(meta)
