from ..resolvers import resolve_products
from ...channel import ChannelQsContext


def resolve_ticket_products(info, requestor, channel_slug=None, **_kwargs) -> ChannelQsContext:
    return resolve_products(info, requestor, channel_slug, **_kwargs)
