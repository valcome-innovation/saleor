from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from graphql_relay import from_global_id

from . import stream_settings
from .models import StreamTicket, AccessState
from ..checkout.models import Checkout
from ..core.models import ModelWithMetadata
from ..order.error_codes import OrderErrorCode
from ..order.models import Order
from ..payment import ChargeStatus
from ..payment.models import Payment
from ..product import models

TEAMS_SLUG = 'teams'
LEAGUES_SLUG = 'leagues'
TICKET_TYPE_SLUG = 'ticket-type'
PRODUCT_SLUG_SLUG = 'product-slug'
TEAM_RESTRICTION_SLUG = 'team-restriction'
STREAM_TYPE_SLUG = 'stream-type'

INVALID_PRODUCT_CONFIGURATION_ERROR = ValidationError(
    "STREAM_PLUGIN: Invalid product configuration in checkout found.",
    code=OrderErrorCode.INVALID.value
)


def create_stream_ticket_from_order(order: "Order") -> "StreamTicket":
    (
        global_product_id,
        game_id,
        video_id,
        season_id,
        team_ids_string,
        league_ids_string,
        stream_type_param,
        expires_param,
        start_time_param
    ) = get_stream_meta(order)

    # load product reference from metadata
    _, product_id = from_global_id(global_product_id)
    product = models.Product.objects.filter(id=product_id).first()

    if product is None:
        raise ValidationError("Cloud not find product during stream ticket creation")

    timed_type = 'none'
    start_time = None
    expires = None

    attributes = product.attributes.all()

    # read attributes directly from product
    stream_type = get_attribute_values(attributes, STREAM_TYPE_SLUG).first().slug
    product_slug = get_attribute_values(attributes, PRODUCT_SLUG_SLUG).first().slug
    ticket_type = get_attribute_values(attributes, TICKET_TYPE_SLUG).first().slug
    team_restriction = get_attribute_values(attributes, TEAM_RESTRICTION_SLUG).first().slug

    if ticket_type == 'timed':
        timed_type = ticket_type
        start_time = get_datetime_from_timestamp_str(start_time_param)
        expires = get_expire_date(start_time, expires_param)

    stream_ticket = StreamTicket()
    stream_ticket.order = order
    stream_ticket.user = order.user
    stream_ticket.game_id = game_id or None
    stream_ticket.video_id = video_id or None
    stream_ticket.season_id = season_id or None
    stream_ticket.league_ids = league_ids_string or None
    stream_ticket.team_ids = team_ids_string or None
    stream_ticket.stream_type = stream_type.lower().capitalize()
    stream_ticket.start_time = start_time
    stream_ticket.expires = expires
    stream_ticket.type = ticket_type
    stream_ticket.timed_type = timed_type
    stream_ticket.product_slug = product_slug
    stream_ticket.team_restriction = team_restriction
    stream_ticket.save()

    return stream_ticket


def get_datetime_from_timestamp_str(timestamp: "str"):
    if timestamp:
        dt = datetime.utcfromtimestamp(int(timestamp))
        return make_aware(dt)
    else:
        return None


def get_expire_date(start_time, expire_type):
    # TODO fix expire time [NWS-771]
    if expire_type == "m":
        return start_time + timedelta(days=stream_settings.MONTH_TICKET_DURATION_DAYS)
    elif expire_type == "d":
        return start_time + timedelta(days=stream_settings.DAY_TICKET_DURATION_DAYS)


def validate_stream_ticket_checkout(checkout: "Checkout", lines: "list"):
    (
        global_product_id,
        game_id,
        video_id,
        season_id,
        team_ids_string,
        league_ids_string,
        stream_type,
        expires,
        start_time
    ) = get_stream_meta(checkout)

    # there can only be one ticket per checkout. Tickets must have attributes
    if len(lines) != 1 and lines[0].variant.product.attributes.count() == 0:
        raise INVALID_PRODUCT_CONFIGURATION_ERROR

    product = lines[0].variant.product
    attributes = lines[0].variant.product.attributes.all()

    ticket_type_attr = get_attribute_values(attributes, TICKET_TYPE_SLUG).first()
    stream_type_attr = get_attribute_values(attributes, STREAM_TYPE_SLUG).first()

    team_attr = get_attribute_values(attributes, TEAMS_SLUG)

    do_attributes_match_type = True
    are_teams_matching = True

    # prevent teams from being altered in meta (single tickets do not need team-attr)
    if ticket_type_attr.slug != 'single' \
            and team_attr is not None \
            and team_attr.first().slug != 'all-teams' \
            and team_attr.count() > 0:
        are_teams_matching = team_ids_string is not None \
                             and team_attr.count() == len(team_ids_string.split(','))

    # check if stream type is matching with metadata
    is_stream_type_matching = stream_type == 'g' and stream_type_attr.slug == 'game' \
                              or stream_type == 'v' and stream_type_attr.slug == 'video'

    # compare if ticket_type is matching with passed meta ids
    is_meta_matching = is_meta_matching_ticket_type(
        ticket_type_attr.slug,
        game_id,
        video_id,
        season_id,
        expires,
        start_time,
        league_ids_string
    )

    _, product_id = from_global_id(global_product_id)

    is_product_matching = product.id == int(product_id)

    if is_product_matching \
            and is_meta_matching \
            and is_stream_type_matching \
            and are_teams_matching \
            and do_attributes_match_type:
        return True
    else:
        raise ValidationError({
            "message": "STREAM_PLUGIN: Could not create valid stream ticket from checkout",
            "is_product_matching": is_product_matching,
            "is_meta_matching": is_meta_matching,
            "is_stream_type_matching": is_stream_type_matching,
            "are_teams_matching": are_teams_matching,
            "do_attributes_match_type": do_attributes_match_type,
        }, code=OrderErrorCode.INVALID.value)


def is_meta_matching_ticket_type(ticket_type,
                                 game_id,
                                 video_id,
                                 season_id,
                                 expires,
                                 start_time,
                                 league_ids):
    if ticket_type == 'single':
        return game_id is not None \
               or video_id is not None
    elif ticket_type == 'season' or ticket_type == 'timed-season':
        return season_id is not None
    elif ticket_type == 'timed':
        return expires is not None \
               and start_time is not None \
               and league_ids is not None


def get_stream_meta(meta_object: "ModelWithMetadata"):
    return from_meta('PRODUCT_ID', meta_object), \
           from_meta('GAME_ID', meta_object), \
           from_meta('VIDEO_ID', meta_object), \
           from_meta('SEASON_ID', meta_object), \
           from_meta('TEAM_IDS', meta_object), \
           from_meta('LEAGUE_IDS', meta_object), \
           from_meta('STREAM_TYPE', meta_object), \
           from_meta('EXPIRES', meta_object), \
           from_meta('START_TIME', meta_object)


def from_meta(key, meta_object: "ModelWithMetadata"):
    return meta_object.get_value_from_metadata(key)


def get_attribute_values(attributes, slug: "str"):
    for attr in attributes:
        if attr.attribute.slug == slug:
            return attr.values


def update_stream_ticket_access_state(payment: "Payment"):
    if payment.order:
        access_state = _get_access_state_from_payment(payment)

        if access_state is not None:
            stream_tickets = StreamTicket.objects.filter(order_id=payment.order.pk)
            _update_access_state(stream_tickets, access_state)


def _get_access_state_from_payment(payment: "Payment") -> AccessState:
    access_state = None

    if payment.charge_status == ChargeStatus.FULLY_REFUNDED:
        access_state = AccessState.FULLY_REFUNDED
    elif payment.charge_status == ChargeStatus.PARTIALLY_REFUNDED:
        access_state = AccessState.PARTIALLY_REFUNDED

    return access_state


def _update_access_state(stream_tickets, access_state: "AccessState"):
    for ticket in stream_tickets:
        ticket.access_state = access_state
        ticket.save()
