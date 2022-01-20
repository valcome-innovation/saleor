import logging
from typing import Optional

from django_countries import countries

from .interface import ShippingMethodData
from .models import ShippingMethod, ShippingMethodChannelListing

logger = logging.getLogger(__name__)


def default_shipping_zone_exists(zone_pk=None):
    from .models import ShippingZone

    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)


def get_countries_without_shipping_zone():
    """Return countries that are not assigned to any shipping zone."""
    from .models import ShippingZone

    covered_countries = set()
    for zone in ShippingZone.objects.all():
        covered_countries.update({c.code for c in zone.countries})
    return (country[0] for country in countries if country[0] not in covered_countries)


def convert_to_shipping_method_data(
    shipping_method: "ShippingMethod", listing: Optional["ShippingMethodChannelListing"]
) -> "ShippingMethodData":
    if listing:
        price = listing.price
        minimum_order_price = listing.minimum_order_price
        maximum_order_price = listing.maximum_order_price
    else:
        price = minimum_order_price = maximum_order_price = None
        logger.error(
            f"Selected shipping method {shipping_method.id} has no channel listing."
        )

    return ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        description=shipping_method.description,
        type=shipping_method.type,
        excluded_products=shipping_method.excluded_products,
        channel_listings=shipping_method.channel_listings,
        minimum_order_weight=shipping_method.minimum_order_weight,
        maximum_order_weight=shipping_method.maximum_order_weight,
        maximum_delivery_days=shipping_method.maximum_delivery_days,
        minimum_delivery_days=shipping_method.minimum_delivery_days,
        metadata=shipping_method.metadata,
        private_metadata=shipping_method.private_metadata,
        price=price,
        minimum_order_price=minimum_order_price,
        maximum_order_price=maximum_order_price,
    )
