from django.core.exceptions import ValidationError

from saleor.attribute.models import AssignedProductAttribute
from .models import StreamTicket
from ..checkout.models import Checkout
from ..core.models import ModelWithMetadata
from ..order.error_codes import OrderErrorCode
from ..order.models import Order

teams_slug = 'teams'
leagues_slug = 'leagues'
ticket_type_slug = 'ticket-type'


def create_stream_ticket_from_order(order: "Order"):
    (game_id, season_id, expires, start_time, team_ids, league_ids) = get_stream_meta(order)

    stream_ticket = StreamTicket()
    stream_ticket.user = order.user
    stream_ticket.game_id = game_id or None
    stream_ticket.season_id = season_id or None
    stream_ticket.start_time = start_time or None
    stream_ticket.expires = expires or None
    stream_ticket.league_ids = league_ids or None
    stream_ticket.team_ids = team_ids or None
    stream_ticket.type = determine_ticket_type(game_id, season_id, expires)

    stream_ticket.save()


def determine_ticket_type(game_id, season_id, expires):
    if game_id is not None and season_id is None and expires is None:
        return 'single'
    elif season_id is not None and expires is None and game_id is None:
        return 'season'
    elif expires is not None and season_id is None and game_id is None:
        return 'timed'
    else:
        raise ValidationError(
            "Could not determine TicketType from input parameters",
            code=OrderErrorCode.INVALID.value
        )


def validate_stream_checkout_with_product(checkout: "Checkout", lines: "list"):
    (game_id, season_id, expires, start_time, team_ids, league_ids) = get_stream_meta(checkout)

    stream_ticket_type = determine_ticket_type(game_id, season_id, expires)

    if len(lines) == 1 and lines[0].variant.product.attributes.count() >= 1:
        attributes = lines[0].variant.product.attributes.all()

        ticket_type_attribute = get_attribute(attributes, ticket_type_slug)

        if ticket_type_attribute.values.count() == 1:
            product_ticket_type = ticket_type_attribute.values.first().slug

            if product_ticket_type == stream_ticket_type:
                return True

    raise ValidationError(
        "Checkout is not a valid StreamTicket purchase",
        code=OrderErrorCode.INVALID.value
    )


def get_stream_meta(meta_object: "ModelWithMetadata"):
    return from_meta('GAME_ID', meta_object), \
           from_meta('SEASON_ID', meta_object), \
           from_meta('EXPIRE', meta_object), \
           from_meta('START_TIME', meta_object), \
           from_meta('TEAM_IDS', meta_object), \
           from_meta('LEAGUE_IDS', meta_object)


def from_meta(key, meta_object: "ModelWithMetadata"):
    return meta_object.get_value_from_metadata(key)


def get_attribute(attributes, slug: "str") -> "AssignedProductAttribute":
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == slug:
            return attr
