from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve
from django.views.decorators.csrf import csrf_exempt

from .core.views import jwks
from .graphql.api import schema
from .graphql.views import GraphQLView
from .payment.gateways.paypal.webhook.views import paypal_webhook
from .payment.gateways.stripe.valcome_webhook.views import stripe_webhook
from .plugins.views import (
    handle_global_plugin_webhook,
    handle_plugin_per_channel_webhook,
    handle_plugin_webhook,
)
from .product.views import digital_product

urlpatterns = [
    # VALCOME [NWS-1244]
    url(r"^webhooks/paypal$", csrf_exempt(paypal_webhook), name="paypal_webhook"),
    # VALCOME
    url(r"^webhooks/stripe$", csrf_exempt(stripe_webhook), name="stripe_webhook"),
    url(r"^graphql/$", csrf_exempt(GraphQLView.as_view(schema=schema)), name="api"),
    url(
        r"^digital-download/(?P<token>[0-9A-Za-z_\-]+)/$",
        digital_product,
        name="digital-product",
    ),
    url(
        r"plugins/channel/(?P<channel_slug>[.0-9A-Za-z_\-]+)/"
        r"(?P<plugin_id>[.0-9A-Za-z_\-]+)/",
        handle_plugin_per_channel_webhook,
        name="plugins-per-channel",
    ),
    url(
        r"plugins/global/(?P<plugin_id>[.0-9A-Za-z_\-]+)/",
        handle_global_plugin_webhook,
        name="plugins-global",
    ),
    url(
        r"plugins/(?P<plugin_id>[.0-9A-Za-z_\-]+)/",
        handle_plugin_webhook,
        name="plugins",
    ),
    url('', include('social_django.urls', namespace='social')),
    url(r".well-known/jwks.json", jwks, name="jwks")
]

if settings.DEBUG:
    import warnings

    from .core import views

    try:
        import debug_toolbar
    except ImportError:
        warnings.warn(
            "The debug toolbar was not installed. Ignore the error. \
            settings.py should already have warned the user about it."
        )
    else:
        urlpatterns += [
            url(r"^__debug__/", include(debug_toolbar.urls))  # type: ignore
        ]

    urlpatterns += static("/media/", document_root=settings.MEDIA_ROOT) + [
        url(r"^static/(?P<path>.*)$", serve),
        url(r"^", views.home, name="home"),
    ]
