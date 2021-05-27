from typing import TYPE_CHECKING, List

from ..stripe import list_client_sources
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ....streaming import stream_settings

from ..utils import get_supported_currencies, require_active_plugin
from . import (
    GatewayConfig,
    create_sofort_payment_intent,
    GatewayResponse,
    PaymentData,
    get_payment_meta,
    process_payment, confirm_payment
)

GATEWAY_NAME = "SOFORT"

if TYPE_CHECKING:
    # flake8: noqa
    from ...interface import CustomerSource, GatewayConfig, GatewayResponse, PaymentData
    from . import  create_sofort_payment_intent


class SofortGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.sofort"
    DEFAULT_ACTIVE = stream_settings.STRIPE_PLUGIN_ACTIVE
    DEFAULT_CONFIGURATION = [
        {"name": "Public API key", "value": stream_settings.STRIPE_PUBLIC_KEY},
        {"name": "Secret API key", "value": stream_settings.STRIPE_PRIVATE_KEY},
        {"name": "Supported currencies", "value": stream_settings.DEFAULT_CURRENCY},
    ]

    CONFIG_STRUCTURE = {
        "Public API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Stripe public API key.",
            "label": "Public API key",
        },
        "Secret API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Stripe secret API key.",
            "label": "Secret API key",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=False,
            supported_currencies=configuration["Supported currencies"],
            connection_params={
                "public_key": configuration["Public API key"],
                "private_key": configuration["Secret API key"],
            }
        )

    def _get_gateway_config(self):
        return self.config

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return confirm_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        sources = list_client_sources(self._get_gateway_config(), customer_id)
        previous_value.extend(sources)
        return previous_value

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {"field": "api_key", "value": config.connection_params["public_key"]},
            {"field": "store_customer_card", "value": config.store_customer},
        ]

    @require_active_plugin
    def get_payment_meta(self, payment_intent_id):
        config = self._get_gateway_config()
        return get_payment_meta(config, payment_intent_id)
