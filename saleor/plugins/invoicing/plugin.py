from typing import Any, Optional
from uuid import uuid4

from django.core.files.base import ContentFile

from .order_confirmed import create_and_send_invoice
from ...core import JobStatus
from ...invoice.models import Invoice
from ...order.models import Order
from ..base_plugin import BasePlugin, ConfigurationTypeField
from .utils import generate_invoice_number, generate_invoice_pdf


class InvoicingPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.invoicing"
    PLUGIN_NAME = "Invoicing"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = "Built-in saleor plugin that handles invoice creation."
    CONFIGURATION_PER_CHANNEL = False

    # VALCOME
    DEFAULT_CONFIGURATION = [
        {
            "name": "automatic-invoice-creation",
            "value": True,
        }
    ]

    # VALCOME
    CONFIG_STRUCTURE = {
        "automatic-invoice-creation": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Create invoices automatically whenever an order is confirmed "
                         "and also send the invoice via email to the customer",
            "label": "Automatic invoice creation",
        }
    }

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        invoice.update_invoice(number=generate_invoice_number())
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
        return invoice

    def order_confirmed(self, order: "Order", previous_value: Any):
        configuration = {item["name"]: item["value"] for item in self.configuration}

        if configuration["automatic-invoice-creation"]:
            create_and_send_invoice(order)
