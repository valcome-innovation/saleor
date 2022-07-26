from typing import TYPE_CHECKING, Optional
from datetime import datetime
import pytz

from ..core.notifications import get_site_context
from ..core.notify_events import NotifyEventType

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App
    from ..plugins.manager import PluginsManager
    from .models import Invoice


def get_invoice_payload(invoice):
    return {
        "id": invoice.id,
        "number": invoice.number,
        "download_url": invoice.url,
        "order_id": invoice.order_id,
    }


def get_order_payload(order):
    return {
        "id": order.id,
        "total_net_amount": order.total_net_amount,
        "total_gross_amount": order.total_gross_amount,
        "currency": order.currency,
        "display_gross_prices": order.display_gross_prices
    }


def send_invoice(
    invoice: "Invoice",
    staff_user: "User",
    app: Optional["App"],
    manager: "PluginsManager",
):
    """Send an invoice to user of related order with URL to download it."""
    payload = {
        "invoice": get_invoice_payload(invoice),
        "order": get_order_payload(invoice.order),
        "creation_date": datetime.now(tz=pytz.utc).strftime("%d %b %Y"),
        "recipient_email": invoice.order.get_customer_email(),  # type: ignore
        "requester_user_id": staff_user.id,
        "requester_app_id": app.id if app else None,
        **get_site_context(),
    }

    channel_slug = None
    if invoice.order and invoice.order.channel:
        channel_slug = invoice.order.channel.slug
    manager.notify(
        NotifyEventType.INVOICE_READY, payload, channel_slug=channel_slug
    )  # type: ignore
    manager.invoice_sent(invoice, invoice.order.get_customer_email())  # type: ignore
