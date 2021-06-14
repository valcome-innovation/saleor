from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection

from saleor.attribute.models import Attribute, AttributeProduct, AttributeValue, \
    AttributeVariant, AttributePage, AssignedProductAttribute, AssignedPageAttribute, \
    AssignedVariantAttribute
from saleor.product.models import Product, ProductVariant, ProductVariantChannelListing, \
    ProductChannelListing


class Command(BaseCommand):
    help = "Reset sequences after product generation"

    def handle(self, *args, **options):
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), [
            Product,
            ProductVariant,
            ProductVariantChannelListing,
            ProductChannelListing,
            Attribute,
            AttributeProduct,
            AttributeValue,
            AttributeVariant,
            AttributePage,
            AssignedProductAttribute,
            AssignedPageAttribute,
            AssignedVariantAttribute,
        ])
        with connection.cursor() as cursor:
            for sql in sequence_sql:
                cursor.execute(sql)
