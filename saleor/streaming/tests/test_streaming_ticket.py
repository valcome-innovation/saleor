import pytest

from saleor.order.models import Order
from saleor.streaming.models import StreamTicket
from saleor.streaming.stream_ticket import create_stream_ticket_from_order


stream_ticket_test_data = [
    ({'GAME_ID': 1234}, {'game_id': 1234}, 'single'),
    ({'SEASON_ID': 11, 'TEAM_ID': 22}, {'season_id': 11, 'team_id': 22}, 'team'),
    ({'SEASON_ID': 11}, {'season_id': 11}, 'league'),
]


@pytest.mark.parametrize('meta,query,expected', stream_ticket_test_data)
def test_create_single_stream_ticket(order_with_lines: "Order", meta, query, expected):
    order = order_with_lines
    order.store_value_in_metadata(meta)

    create_stream_ticket_from_order(order)

    stream_ticket = StreamTicket.objects.filter(**query).first()
    assert stream_ticket.type == expected
