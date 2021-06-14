from django.contrib.sites.models import Site

from .. import settings
from ..account.models import Address
from ..streaming import stream_settings


def get_site_context():
    site: Site = Site.objects.get_current()
    site_context = {
        "domain": site.domain,
        "site_name": site.name,
        "static_url": settings.STATIC_URL,
        "support_email": stream_settings.SUPPORT_EMAIL
    }
    return site_context


def get_site_address():
    site: Site = Site.objects.get_current()
    address: "Address" = site.settings.company_address
    site_address = {
        "company_address": {
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "country": address.country.name,
            "city": address.city,
            "postal_code": address.postal_code,
            "phone": address.phone,
            "uid": stream_settings.UID
        }
    }
    return site_address
