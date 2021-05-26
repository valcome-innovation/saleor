from .plugin import SofortGatewayPlugin
from ....plugins import manager


def resolve_payment_meta(payment_intent_id):
    stripe_plugin = manager.get_plugins_manager().get_plugin("mirumee.payments.sofort")
    if isinstance(stripe_plugin, SofortGatewayPlugin):
        return stripe_plugin.get_payment_meta(payment_intent_id)
