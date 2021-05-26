import graphene

from ...channel.models import Channel
from ...core.exceptions import PermissionDenied
from ...core.tracing import traced_resolver
from ...order import OrderStatus, models
from ...order.events import OrderEvents
from ...order.models import OrderEvent
from ...order.utils import sum_order_totals
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..utils.filters import filter_by_period
from .types import Order

ORDER_SEARCH_FIELDS = ("id", "discount_name", "token", "user_email", "user__email")


@traced_resolver
def resolve_orders(_info, channel_slug, **_kwargs):
    qs = models.Order.objects.non_draft()
    if channel_slug:
        qs = qs.filter(channel__slug=str(channel_slug))
    return qs


@traced_resolver
def resolve_draft_orders(_info, **_kwargs):
    qs = models.Order.objects.drafts()
    return qs


@traced_resolver
def resolve_orders_total(_info, period, channel_slug):
    if channel_slug is None:
        channel_slug = get_default_channel_slug_or_graphql_error()
    channel = Channel.objects.filter(slug=str(channel_slug)).first()
    if not channel:
        return None
    qs = (
        models.Order.objects.non_draft()
        .exclude(status=OrderStatus.CANCELED)
        .filter(channel__slug=str(channel_slug))
    )
    qs = filter_by_period(qs, period, "created")
    return sum_order_totals(qs, channel.currency_code)


@traced_resolver
def resolve_order(info, order_id):
    return graphene.Node.get_node_from_global_id(info, order_id, Order)


def resolve_homepage_events():
    # Filter only selected events to be displayed on homepage.
    types = [
        OrderEvents.PLACED,
        OrderEvents.PLACED_FROM_DRAFT,
        OrderEvents.ORDER_FULLY_PAID,
    ]
    return OrderEvent.objects.filter(type__in=types)


def resolve_order_by_token(token):
    return (
        models.Order.objects.exclude(status=OrderStatus.DRAFT)
        .filter(token=token)
        .first()
    )


def resolve_order_exists(info, checkout_token):
    user = info.context.user
    if user is not None and user.is_authenticated:
        return models.Order.objects.filter(checkout_token=checkout_token).exists()
    else:
        raise PermissionDenied()
