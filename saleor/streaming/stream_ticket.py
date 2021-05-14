from django.core.exceptions import ValidationError

from .models import StreamTicket
from ..core.models import ModelWithMetadata
from ..order.error_codes import OrderErrorCode
from ..order.models import Order


def create_stream_ticket_from_order(order: "Order"):
    (game_id, season_id, team_id) = get_stream_meta(order)
    expires = None  # TODO: set expires for day ticket

    stream_ticket = StreamTicket()
    stream_ticket.user = order.user
    stream_ticket.game_id = game_id or None
    stream_ticket.season_id = season_id or None
    stream_ticket.team_id = team_id or None
    stream_ticket.expires = expires
    stream_ticket.type = determine_ticket_type(game_id, season_id, team_id, expires)

    stream_ticket.save()


def determine_ticket_type(game_id, season_id, team_id, expires):
    if game_id is not None and season_id is None and team_id is None:
        return 'single'
    elif season_id is not None and team_id is not None and game_id is None:
        return 'team'
    elif season_id is not None and team_id is None and game_id is None:
        return 'league'
    elif expires is not None and season_id is None and team_id is None and game_id is None:
        return 'day'
    else:
        raise ValidationError(
            "Could not determine TicketType from input parameters",
            code=OrderErrorCode.INVALID.value
        )


def validate_stream_checkout_with_product(checkout, lines):
    (game_id, season_id, team_id) = get_stream_meta(checkout)
    stream_ticket_type = determine_ticket_type(game_id, season_id, team_id, None)

    if len(lines) == 1 and lines[0].variant.product.attributes.count() >= 1:
        attributes = lines[0].variant.product.attributes.all()
        attribute = get_stream_type_attribute(attributes)

        if attribute.values.count() == 1 and has_team_attribute(attributes):
            product_ticket_type = attribute.values.first().slug

            if product_ticket_type == stream_ticket_type:
                return True

    raise ValidationError(
        "Checkout is not a valid StreamTicket purchase",
        code=OrderErrorCode.INVALID.value
    )


def get_stream_meta(meta_object: "ModelWithMetadata"):
    return from_meta('GAME_ID', meta_object), \
           from_meta('SEASON_ID', meta_object), \
           from_meta('TEAM_ID', meta_object)


def from_meta(key, meta_object: "ModelWithMetadata"):
    return meta_object.get_value_from_metadata(key)


def get_stream_type_attribute(attributes):
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == 'stream-type':
            return attr


def has_team_attribute(attributes):
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == 'team':
            return True

    return False
