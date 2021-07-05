from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from . import stream_settings
from ..attribute.models import AssignedProductAttribute
from .models import StreamTicket
from ..checkout.models import Checkout
from ..core.models import ModelWithMetadata
from ..order.error_codes import OrderErrorCode
from ..order.models import Order

teams_slug = 'teams'
leagues_slug = 'leagues'
ticket_type_slug = 'ticket-type'


def create_stream_ticket_from_order(order: "Order") -> "StreamTicket":
    (game_id, season_id, expires, start_time, team_ids, league_ids) = get_stream_meta(order)

    stream_ticket = StreamTicket()
    stream_ticket.user = order.user
    stream_ticket.game_id = game_id or None
    stream_ticket.season_id = season_id or None
    stream_ticket.league_ids = league_ids or None
    stream_ticket.team_ids = team_ids or None
    stream_ticket.start_time = get_datetime_from_timestamp_str(start_time)
    stream_ticket.expires = get_expire_date(stream_ticket.start_time, expires)
    stream_ticket.type = determine_stream_ticket_type(game_id, season_id, expires)
    stream_ticket.timed_type = determine_timed_type(stream_ticket.type, expires)

    validate_stream_ticket_creation(stream_ticket)
    stream_ticket.save()
    return stream_ticket


def get_datetime_from_timestamp_str(timestamp: "str"):
    if timestamp:
        dt = datetime.utcfromtimestamp(int(timestamp))
        return make_aware(dt)
    else:
        return None


def validate_stream_ticket_creation(stream_ticket: "StreamTicket"):
    validate_start_time(stream_ticket.start_time)


def validate_start_time(start_time: "datetime"):
    if start_time:
        start_date = start_time.date()
        utc_now_date = datetime.utcnow().date()
        day_difference = (start_date - utc_now_date).days

        if day_difference < 0:
            raise ValidationError(
                "Start-Time cannot be in the past for newly purchased tickets."
            )
    return True


def determine_stream_ticket_type(game_id, season_id, expires):
    if game_id is not None and season_id is None and expires is None:
        return "single"
    elif season_id is not None and expires is None and game_id is None:
        return "season"
    elif expires is not None and season_id is None and game_id is None:
        return "timed"
    else:
        raise ValidationError(
            "Could not determine TicketType from input parameters",
            code=OrderErrorCode.INVALID.value
        )


def determine_timed_type(ticket_type, expire):
    if ticket_type == "timed":
        if expire == "m":
            return "month"
        else:
            return "day"
    else:
        return "none"


def get_expire_date(start_time, expire_type):
    # TODO fix expire time [NWS-771]
    if expire_type == "m":
        return start_time + timedelta(days=stream_settings.MONTH_TICKET_DURATION_DAYS)
    elif expire_type == "d":
        return start_time + timedelta(days=stream_settings.DAY_TICKET_DURATION_DAYS)


def validate_stream_checkout_with_product(checkout: "Checkout", lines: "list"):
    (game_id, season_id, expires, start_time, team_ids, league_ids) = get_stream_meta(checkout)

    ticket_type = determine_stream_ticket_type(game_id, season_id, expires)
    timed_type = determine_timed_type(ticket_type, expires)

    if len(lines) == 1 and lines[0].variant.product.attributes.count() >= 1:
        attributes = lines[0].variant.product.attributes.all()
        ticket_type_attribute = get_attribute(attributes, ticket_type_slug)

        if ticket_type_attribute.values.count() == 1:
            product_ticket_type = ticket_type_attribute.values.first().slug

            return product_ticket_type_matches_purchased_ticket(
                product_ticket_type, ticket_type, timed_type
            )

    raise ValidationError(
        "Checkout is not a valid StreamTicket purchase",
        code=OrderErrorCode.INVALID.value
    )


def product_ticket_type_matches_purchased_ticket(product_ticket_type, ticket_type, timed_type):
    return product_ticket_type is not None and \
        product_ticket_type in [ticket_type, timed_type]


def get_stream_meta(meta_object: "ModelWithMetadata"):
    return from_meta('GAME_ID', meta_object), \
           from_meta('SEASON_ID', meta_object), \
           from_meta('EXPIRES', meta_object), \
           from_meta('START_TIME', meta_object), \
           from_meta('TEAM_IDS', meta_object), \
           from_meta('LEAGUE_IDS', meta_object)


def from_meta(key, meta_object: "ModelWithMetadata"):
    return meta_object.get_value_from_metadata(key)


def get_attribute(attributes, slug: "str") -> "AssignedProductAttribute":
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == slug:
            return attr
