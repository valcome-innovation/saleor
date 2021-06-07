from uuid import uuid4

from django.core.files.base import ContentFile

from ..manager import get_plugins_manager
from ...core import JobStatus
from ...invoice.models import Invoice
from ...invoice.notifications import send_invoice
from ...order import events as order_events
from ...order.models import Order
from .utils import generate_invoice_number, generate_invoice_pdf


def create_and_send_invoice(order: "Order"):
    number=generate_invoice_number()
    invoice = Invoice.objects.create(
        order=order, number=number,
    )

    file_content, creation_date = generate_invoice_pdf(invoice)
    invoice.created = creation_date
    invoice.invoice_file.save(
        f"invoice-{invoice.number}-order-{order.id}-{uuid4()}.pdf",
        ContentFile(file_content),
    )
    invoice.status = JobStatus.SUCCESS
    invoice.save(
        update_fields=["created", "number", "invoice_file", "status", "updated_at"]
    )

    order_events.invoice_generated_event(
        order=order,
        user=order.user,
        invoice_number=invoice.number,
    )

    manager = get_plugins_manager()
    send_invoice(invoice, order.user, manager)
