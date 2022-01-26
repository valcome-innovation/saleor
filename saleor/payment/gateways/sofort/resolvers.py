import json

from .plugin import SofortGatewayPlugin
from ....plugins import manager


def resolve_payment_meta(payment_intent_id):
    sofort_plugin = manager.get_plugins_manager().get_plugin("mirumee.payments.sofort")

    if isinstance(sofort_plugin, SofortGatewayPlugin):
        meta = sofort_plugin.get_payment_meta(payment_intent_id)

        return json.dumps(meta)
