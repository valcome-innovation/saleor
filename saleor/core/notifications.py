from django.contrib.sites.models import Site

from .. import settings
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
