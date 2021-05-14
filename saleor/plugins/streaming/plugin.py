from typing import Any, List, Optional, Iterable
import logging

from ..base_plugin import BasePlugin
from ...checkout.fetch import CheckoutLineInfo, CheckoutInfo
from ...discount import DiscountInfo
from ...order.models import Order
from ...streaming.stream_ticket import validate_stream_checkout_with_product, \
    create_stream_ticket_from_order
from ...streaming.user_watch_log import create_user_watch_log_from_order

logger = logging.getLogger(__name__)


class StreamingPlugin(BasePlugin):

    PLUGIN_ID = "valcome.streaming"
    PLUGIN_NAME = "Streaming"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Enables the creation of stream tickets and user watch logs during the order "
        "creation process"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def preprocess_order_creation(self, checkout_info: "CheckoutInfo",
                                  discounts: List["DiscountInfo"],
                                  lines: Optional[Iterable["CheckoutLineInfo"]],
                                  previous_value: Any):
        checkout_lines = map(lambda line: line.line, lines)
        
        validate_stream_checkout_with_product(
            checkout_info.checkout,
            list(checkout_lines)
        )

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        try:
            create_stream_ticket_from_order(order)
            create_user_watch_log_from_order(order)
        except Exception as exc:
            logger.exception(
                f"[stream checkout] FATAL error after creating order with id {order.pk}",
                exc_info=exc
            )
