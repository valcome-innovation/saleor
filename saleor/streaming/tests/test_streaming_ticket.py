from datetime import datetime
from django.core.exceptions import ValidationError

import graphene
import pytest

from ...order.models import Order
from ...streaming.stream_ticket import (
    create_stream_ticket_from_order, validate_stream_ticket_checkout,
)

now_string = '%d' % datetime.utcnow().timestamp()


def test_create_single_ticket(single_ticket_order: "Order"):
    stream_ticket = create_stream_ticket_from_order(single_ticket_order)

    assert stream_ticket.stream_type == 'Game'
    assert stream_ticket.product_slug == 'single'
    assert stream_ticket.type == 'single'
    assert stream_ticket.timed_type == 'none'
    assert stream_ticket.game_id == 'gameId'
    assert stream_ticket.expires is None
    assert stream_ticket.start_time is None


def test_create_season_ticket(season_ticket_order: "Order"):
    stream_ticket = create_stream_ticket_from_order(season_ticket_order)

    assert stream_ticket.stream_type == 'Game'
    assert stream_ticket.product_slug == 'cup'
    assert stream_ticket.type == 'season'
    assert stream_ticket.timed_type == 'none'
    assert stream_ticket.season_id == 'seasonId'
    assert stream_ticket.expires is None
    assert stream_ticket.start_time is None


def test_create_timed_season_ticket(timed_season_ticket_order: "Order"):
    expected_start = datetime.fromisoformat('2022-09-01 00:00:00.000000+00:00')
    expected_end = datetime.fromisoformat('2023-02-01 00:00:00.000000+00:00')

    stream_ticket = create_stream_ticket_from_order(timed_season_ticket_order)

    assert stream_ticket.stream_type == 'Game'
    assert stream_ticket.product_slug == 'regular-season'
    assert stream_ticket.type == 'timed-season'
    assert stream_ticket.timed_type == 'none'
    assert stream_ticket.season_id == 'seasonId'
    assert stream_ticket.start_time == expected_start
    assert stream_ticket.expires == expected_end


def test_single_ticket_validation(single_ticket_checkout):
    [checkout, lines] = single_ticket_checkout

    actual = validate_stream_ticket_checkout(
        checkout,
        lines
    )

    assert actual is True


def test_season_ticket_validation(season_ticket_checkout):
    [checkout, lines] = season_ticket_checkout

    actual = validate_stream_ticket_checkout(
        checkout,
        lines
    )

    assert actual is True


def test_timed_season_ticket_validation(timed_season_ticket_checkout):
    [checkout, lines] = timed_season_ticket_checkout

    actual = validate_stream_ticket_checkout(
        checkout,
        lines
    )

    assert actual is True


def test_team_timed_season_ticket_validation(team_timed_season_ticket_checkout):
    [checkout, lines] = team_timed_season_ticket_checkout

    actual = validate_stream_ticket_checkout(
        checkout,
        lines
    )

    assert actual is True


def test_invalid_config(timed_season_ticket_checkout):
    [checkout, lines] = timed_season_ticket_checkout
    checkout.store_value_in_metadata({
        'PRODUCT_ID':  graphene.Node.to_global_id("Product", 1),
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g'
    })

    with pytest.raises(ValidationError):
        validate_stream_ticket_checkout(
            checkout,
            lines
        )
