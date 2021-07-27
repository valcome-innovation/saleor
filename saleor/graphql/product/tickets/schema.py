import graphene

from .filters import TicketProductFilterInput
from .resolvers import resolve_ticket_products
from ..sorters import ProductOrder
from ..types import Product
from ...core.fields import ChannelContextFilterConnectionField


class TicketProductQueries(graphene.ObjectType):
    ticket_products = ChannelContextFilterConnectionField(
        Product,
        filter=TicketProductFilterInput(description="Ticket Product Filter"),
        sort_by=ProductOrder(description="Sort products."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's products.",
    )

    def resolve_ticket_products(self, info, channel=None, **kwargs):
        return resolve_ticket_products(info, info.context.user, channel_slug=channel, **kwargs)
