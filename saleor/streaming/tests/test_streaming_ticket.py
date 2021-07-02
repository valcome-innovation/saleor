import pytest
from django.core.exceptions import ValidationError

from ...order.models import Order
from ...streaming.stream_ticket import (
    create_stream_ticket_from_order,
    get_datetime_from_timestamp_str, determine_stream_ticket_type, determine_timed_type,
    product_ticket_type_matches_purchased_ticket,
)
from ...tests import settings

stream_ticket_test_data = [
    ({'GAME_ID': 1234}, 'single', 'none'),
    ({'SEASON_ID': 11, 'TEAM_IDS': [22]}, 'season', 'none'),
    ({'SEASON_ID': 11}, 'season', 'none'),
    ({'LEAGUE_IDS': [1], 'EXPIRES': 'm', 'START_TIME': '1625232262'}, 'timed', 'month'),
    ({'LEAGUE_IDS': [1], 'EXPIRES': 'd', 'START_TIME': '1625232262'}, 'timed', 'day'),
]


@pytest.mark.parametrize('meta,ticket_type,timed_type', stream_ticket_test_data)
def test_create_single_stream_ticket(order_with_lines: "Order", meta, ticket_type, timed_type):
    order = order_with_lines
    order.store_value_in_metadata(meta)

    stream_ticket = create_stream_ticket_from_order(order)

    assert stream_ticket.type == ticket_type
    assert stream_ticket.timed_type == timed_type


ticket_type_valid_test_data = [
    ("1", None, None, "single"),
    ("2", None, None, "single"),
    (None, "1", None, "season"),
    (None, "2", None, "season"),
    (None, None, "m", "timed"),
    (None, None, "d", "timed"),
]


@pytest.mark.parametrize('game_id,season_id,expires,type', ticket_type_valid_test_data)
def test_determine_stream_ticket_type(game_id, season_id, expires, type):
    result = determine_stream_ticket_type(game_id, season_id, expires)
    assert result == type


ticket_type_invalid_test_data = [
    ("1", "1", "d"),
    ("1", "1", "m"),
    ("1", "1", None),
    ("1", None, "d"),
    ("1", None, "m"),
    (None, "1", "m"),
    (None, "1", "d"),
]


@pytest.mark.parametrize('game_id,season_id,expires', ticket_type_invalid_test_data)
def test_determine_stream_ticket_type_invalid(game_id, season_id, expires):
    with pytest.raises(ValidationError):
        determine_stream_ticket_type(game_id, season_id, expires)


timed_type_data = [
    ("single", None, 'none'),
    ("season", None, 'none'),
    ("timed", 'm', 'month'),
    ("timed", 'd', 'day'),
    ("wtf", None, 'none'),
    ("wtf", 'd', 'none'),
    ("wtf", 'm', 'none'),
]


@pytest.mark.parametrize('ticket_type,expire,expected_type', timed_type_data)
def test_determine_timed_type(ticket_type, expire, expected_type):
    result = determine_timed_type(ticket_type, expire)
    assert result == expected_type


product_ticket_type_test_data = [
    ("month", "timed", "month", True),
    ("day", "timed", "day", True),
    ("single", "single", "none", True),
    ("season", "season", "none", True),
    ("month", "timed", "day", False),
    ("month", "single", "none", False),
    ("month", "season", "none", False),
    ("day", "timed", "month", False),
    ("day", "single", "none", False),
    ("day", "season", "none", False),
    ("season", "single", "none", False),
    ("season", "timed", "day", False),
    ("season", "timed", "month", False),
    ("single", "season", "none", False),
    ("single", "timed", "day", False),
    ("single", "timed", "month", False),
]


@pytest.mark.parametrize('product_ticket_type,ticket_type,timed_type,expected', product_ticket_type_test_data)
def test_product_ticket_type_matches_purchased_ticket(product_ticket_type, ticket_type, timed_type, expected):
    result = product_ticket_type_matches_purchased_ticket(product_ticket_type, ticket_type, timed_type)
    assert result == expected


def test_get_datetime_from_timestamp_str():
    date = get_datetime_from_timestamp_str("1625232262")
    assert date is not None
    assert date.tzinfo.zone == settings.TIME_ZONE

    date = get_datetime_from_timestamp_str(None)
    assert date is None
