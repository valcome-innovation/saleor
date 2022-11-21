import graphene
import pytest
from datetime import datetime

from saleor.attribute import AttributeType
from saleor.attribute.models import Attribute, AttributeValue
from saleor.attribute.utils import associate_attribute_values_to_instance
from saleor.checkout.models import Checkout, CheckoutLine
from saleor.order.models import Order
from saleor.product.models import Product, ProductVariant


@pytest.fixture
def single_ticket_order(
        order_with_lines: "Order",
        single_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", single_ticket_product.pk)

    order_with_lines.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'GAME_ID': 'gameId',
        'STREAM_TYPE': 'g'
    })

    return order_with_lines


@pytest.fixture
def season_ticket_order(
        order_with_lines: "Order",
        season_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", season_ticket_product.pk)

    order_with_lines.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g'
    })

    return order_with_lines


@pytest.fixture
def timed_season_ticket_order(
        order_with_lines: "Order",
        timed_season_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", timed_season_ticket_product.pk)

    order_with_lines.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g'
    })

    return order_with_lines


@pytest.fixture
def single_ticket_checkout(
        checkout: "Checkout",
        single_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", single_ticket_product.pk)

    checkout.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'GAME_ID': 'gameId',
        'STREAM_TYPE': 'g'
    })

    line = create_checkout_line(single_ticket_product)
    lines = [line]

    return [checkout, lines]


@pytest.fixture
def season_ticket_checkout(
        checkout: "Checkout",
        season_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", season_ticket_product.pk)

    checkout.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g',
        'TEAM_IDS': ''
    })

    line = create_checkout_line(season_ticket_product)
    lines = [line]

    return [checkout, lines]


@pytest.fixture
def timed_season_ticket_checkout(
        checkout: "Checkout",
        timed_season_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product", timed_season_ticket_product.pk)

    checkout.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g',
        'TEAM_IDS': ''
    })

    line = create_checkout_line(timed_season_ticket_product)
    lines = [line]

    return [checkout, lines]


@pytest.fixture
def team_timed_season_ticket_checkout(
        checkout: "Checkout",
        team_timed_season_ticket_product: "Product"
):
    product_id = graphene.Node.to_global_id("Product",
                                            team_timed_season_ticket_product.pk)

    checkout.store_value_in_metadata({
        'PRODUCT_ID': product_id,
        'SEASON_ID': 'seasonId',
        'STREAM_TYPE': 'g',
        'TEAM_IDS': ['team1', 'team2']
    })

    line = create_checkout_line(team_timed_season_ticket_product)
    lines = [line]

    return [checkout, lines]


@pytest.fixture
def single_ticket_product(product: "Product"):
    stream_type = create_attribute('stream-type', 'game')
    product_slug = create_attribute('product-slug', 'single')
    ticket_type = create_attribute('ticket-type', 'single')

    assign_attributes(product, [stream_type, product_slug, ticket_type])
    product.save()

    return product


@pytest.fixture
def season_ticket_product(product: "Product"):
    stream_type = create_attribute('stream-type', 'game')
    product_slug = create_attribute('product-slug', 'cup')
    ticket_type = create_attribute('ticket-type', 'season')
    teams = create_attribute('teams', 'all-teams')

    assign_attributes(product, [stream_type, product_slug, ticket_type, teams])
    product.save()

    return product


@pytest.fixture
def base_timed_season_ticket_product(product: "Product"):
    start_date = datetime.fromisoformat('2022-09-01 00:00:00.000000+00:00')
    end_date = datetime.fromisoformat('2023-02-01 00:00:00.000000+00:00')

    stream_type = create_attribute('stream-type', 'game')
    product_slug = create_attribute('product-slug', 'regular-season')
    ticket_type = create_attribute('ticket-type', 'timed-season')
    start_date_attr = create_attribute('start-date', 'start-date', start_date)
    end_date_attr = create_attribute('end-date', 'end-date', end_date)

    assign_attributes(product, [
        stream_type, product_slug, ticket_type, start_date_attr, end_date_attr
    ])

    return product


@pytest.fixture
def timed_season_ticket_product(base_timed_season_ticket_product: "Product"):
    teams = create_attribute('teams', 'all-teams')

    assign_attributes(base_timed_season_ticket_product, [teams])
    base_timed_season_ticket_product.save()

    return base_timed_season_ticket_product


@pytest.fixture
def team_timed_season_ticket_product(base_timed_season_ticket_product: "Product"):
    team_attribute = create_attribute('teams', 'team1')
    AttributeValue.objects.create(attribute=team_attribute, name='team2', slug='team2')

    assign_attributes(base_timed_season_ticket_product, [team_attribute])
    base_timed_season_ticket_product.save()

    return base_timed_season_ticket_product


def create_checkout_line(product: "Product"):
    line = CheckoutLine()
    line.variant = ProductVariant()
    line.variant.product = product

    product.save()

    return line


def assign_attributes(product, attributes):
    for attr in attributes:
        product.product_type.product_attributes.add(attr)
        all_attrs = attr.values.all()

        associate_attribute_values_to_instance(
            product,
            attr,
            *all_attrs
        )

    return product


def create_attribute(name, value, date_time=None):
    attribute = Attribute.objects.create(
        slug=name,
        name=name,
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    AttributeValue.objects.create(
        attribute=attribute,
        name=value,
        slug=value,
        date_time=date_time
    )

    return attribute
