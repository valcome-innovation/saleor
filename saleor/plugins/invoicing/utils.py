import os
import re
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase

import pytz
from django.conf import settings
from django.template.loader import get_template
from weasyprint import HTML

from ...core.notifications import get_site_address
from ...invoice.models import Invoice
from ...streaming import stream_settings

MAX_PRODUCTS_WITH_TABLE = 3
MAX_PRODUCTS_WITHOUT_TABLE = 4
MAX_PRODUCTS_PER_PAGE = 13


def make_full_invoice_number(number=None, month=None, year=None):
    now = datetime.now()
    current_month = int(now.strftime("%m"))
    current_year = int(now.strftime("%Y"))
    month_and_year = now.strftime("%m/%Y")

    if month == current_month and year == current_year:
        new_number = (number or 0) + 1
        return f"{new_number}/{month_and_year}"
    return f"1/{month_and_year}"


def parse_invoice_dates(invoice):
    match = re.match(r"^(\d+)\/(\d+)\/(\d+)", invoice.number)
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def generate_invoice_number():
    last_invoice = Invoice.objects.filter(number__isnull=False).last()
    if not last_invoice or not last_invoice.number:
        return make_full_invoice_number()

    try:
        number, month, year = parse_invoice_dates(last_invoice)
        return make_full_invoice_number(number, month, year)
    except (IndexError, ValueError, AttributeError):
        return make_full_invoice_number()


def chunk_products(products, product_limit):
    """Split products to list of chunks.

    Each chunk represents products per page, product_limit defines chunk size.
    """
    chunks = []
    for i in range(0, len(products), product_limit):
        limit = i + product_limit
        chunks.append(products[i:limit])
    return chunks


def get_product_limit_first_page(products):
    if len(products) < MAX_PRODUCTS_WITHOUT_TABLE:
        return MAX_PRODUCTS_WITH_TABLE

    return MAX_PRODUCTS_WITHOUT_TABLE


def generate_invoice_pdf(invoice):
    font_path = os.path.join(
        settings.PROJECT_ROOT, "templates", "invoices", "inter.ttf"
    )

    all_products = invoice.order.lines.all()

    product_limit_first_page = get_product_limit_first_page(all_products)

    products_first_page = all_products[:product_limit_first_page]
    rest_of_products = chunk_products(
        all_products[product_limit_first_page:], MAX_PRODUCTS_PER_PAGE
    )
    creation_date = datetime.now(tz=pytz.utc)
    rendered_template = get_template("invoices/invoice.html").render(
        {
            "invoice": invoice,
            "creation_date": creation_date.strftime("%d %b %Y"),
            "order": invoice.order,
            "font_path": f"file://{font_path}",
            "products_first_page": products_first_page,
            "rest_of_products": rest_of_products,
            "support_email": stream_settings.SUPPORT_EMAIL,
            **get_site_address(),
        }
    )
    return HTML(string=rendered_template).write_pdf(), creation_date


# VALCOME
def get_invoice_attachment(invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)
    invoice_pdf, date = generate_invoice_pdf(invoice)
    f = MIMEBase("application", "octate-stream", Name="invoice.pdf")
    f.set_payload(invoice_pdf)
    encoders.encode_base64(f)
    f.add_header('Content-Decomposition', 'attachment', filename="invoice.pdf")
    return f
