from django.core.exceptions import ValidationError
from ..account.models import StreamTicket
from ..account.error_codes import AccountErrorCode


def has_stream_meta(checkout):
    game_id = from_meta('GAME_ID', checkout)
    season_id = from_meta('SEASON_ID', checkout)
    team_id = from_meta('TEAM_ID', checkout)
    return game_id is not None or season_id is not None or team_id is not None


def from_meta(key, checkout):
    return checkout.get_value_from_metadata(key, None)


def create_stream_ticket_from_checkout(user, checkout):
    lines = list(checkout)
    game_id = from_meta('GAME_ID', checkout)
    season_id = from_meta('SEASON_ID', checkout)
    team_id = from_meta('TEAM_ID', checkout)
    create_stream_ticket_for_user(user, lines, game_id, season_id, team_id, None)


def create_stream_ticket_for_user(user, lines, game_id, season_id, team_id, expires):
    stream_ticket = StreamTicket()
    stream_ticket.user = user
    stream_ticket.game_id = game_id or None
    stream_ticket.season_id = season_id or None
    stream_ticket.team_id = team_id or None
    stream_ticket.expires = expires  # TODO: set expires for day ticket
    stream_ticket.type = determine_ticket_type(game_id, season_id, team_id, expires)
    validate_stream_ticket_with_product(stream_ticket, lines)
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
            code=AccountErrorCode.INVALID
        )


def validate_stream_ticket_with_product(stream_ticket, lines):
    if len(lines) == 1 and lines[0].variant.product.attributes.count() >= 1:
        attributes = lines[0].variant.product.attributes.all()
        attribute = get_stream_type_attribute(attributes)
        if attribute.values.count() == 1 and has_team_attribute(attributes):
            product_ticket_type = attribute.values.first().slug
            stream_ticket_type = stream_ticket.type
            if product_ticket_type == stream_ticket_type:
                return True

    raise ValidationError(
        "Checkout is not a valid StreamTicket purchase", code=AccountErrorCode.INVALID
    )


def get_stream_type_attribute(attributes):
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == 'stream-type':
            return attr


def has_team_attribute(attributes):
    for attr in attributes:
        if attr.values.count() == 1 and attr.attribute.slug == 'team':
            return True
    return False
