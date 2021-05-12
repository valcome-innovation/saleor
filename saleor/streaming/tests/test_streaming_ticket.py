from saleor.order.models import Order
from saleor.streaming.models import StreamTicket
from saleor.streaming.stream_ticket import create_stream_ticket_from_order


def test_create_stream_ticket(order_with_lines: "Order"):
    order = order_with_lines
    order.store_value_in_metadata({'GAME_ID': 1234})

    create_stream_ticket_from_order(order)

    stream_ticket = StreamTicket.objects.get(game_id=1234)
    assert stream_ticket.type == 'single'
