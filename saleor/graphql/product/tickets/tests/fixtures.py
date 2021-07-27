import pytest
import datetime
import uuid

from decimal import Decimal
from .....attribute import AttributeType
from .....attribute.models import (
    Attribute, AttributeValue, AttributeProduct, AssignedProductAttribute,
    AssignedProductAttributeValue, AssignedVariantAttribute,
    AssignedVariantAttributeValue, AttributeVariant
)
from .....product.models import (
    ProductType, Product, ProductChannelListing, ProductVariantChannelListing,
    ProductVariant
)


@pytest.fixture
def ticket_products_for_filtering(category, channel_EUR):
    product_type = ProductType.objects.create(name="Ticket")

    ticket_type_attr = Attribute.objects.create(
        slug="ticket-type",
        name="Ticket Type",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True
    )
    type_day = AttributeValue.objects.create(attribute=ticket_type_attr, name="Day", slug="day")
    type_single = AttributeValue.objects.create(attribute=ticket_type_attr, name="Single", slug="single")
    type_month = AttributeValue.objects.create(attribute=ticket_type_attr, name="Month", slug="month")
    type_season = AttributeValue.objects.create(attribute=ticket_type_attr, name="Season", slug="season")

    teams_attribute = Attribute.objects.create(
        slug="teams",
        name="Teams",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True
    )
    team_swl = AttributeValue.objects.create(attribute=teams_attribute, name="SWL", slug="swl")
    team_ka2 = AttributeValue.objects.create(attribute=teams_attribute, name="KA2", slug="ka2")
    team_ash = AttributeValue.objects.create(attribute=teams_attribute, name="ASH", slug="ash")
    team_all = AttributeValue.objects.create(attribute=teams_attribute, name="All Teams", slug="all-teams")

    leagues_attribute = Attribute.objects.create(
        slug="leagues",
        name="Leagues",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True
    )
    league_20_21 = AttributeValue.objects.create(attribute=leagues_attribute, name="AHL 2020/21", slug="ahl-20-21")
    league_21_22 = AttributeValue.objects.create(attribute=leagues_attribute, name="AHL 2021/22", slug="ahl-21-22")

    single_swl, v_single_swl = create_product_with_variant("single-swl", category, product_type, channel_EUR)
    single_ka2, v_single_ka2 = create_product_with_variant("single-ka2", category, product_type, channel_EUR)
    single_ash, v_single_ash = create_product_with_variant("single-ash", category, product_type, channel_EUR)
    month_swl, v_month_swl = create_product_with_variant("month-ahl-20-21-swl", category, product_type, channel_EUR)
    month_ka2, v_month_ka2 = create_product_with_variant("month-ahl-20-21-ka2", category, product_type, channel_EUR)
    month_ash, v_month_ash = create_product_with_variant("month-ahl-20-21-ash", category, product_type, channel_EUR)
    season_swl, v_season_swl = create_product_with_variant("season-ahl-20-21-swl", category, product_type, channel_EUR)
    season_ka2, v_season_ka2 = create_product_with_variant("season-ahl-20-21-ka2", category, product_type, channel_EUR)
    season_ash, v_season_ash = create_product_with_variant("season-ahl-20-21-ash", category, product_type, channel_EUR)
    day_ahl_20_21, v_day_ahl_20_21 = create_product_with_variant("day-ahl-20-21", category, product_type, channel_EUR)
    month_ahl_20_21, v_month_ahl_20_21 = create_product_with_variant("month-ahl-20-21", category, product_type, channel_EUR)
    season_ahl_20_21, v_season_ahl_20_21 = create_product_with_variant("season-ahl-20-21", category, product_type, channel_EUR)

    tickets = [
        single_swl, single_ash, single_ka2,
        month_swl, month_ash, month_ka2, month_ahl_20_21,
        season_swl, season_ash, season_ka2, season_ahl_20_21,
        day_ahl_20_21
    ]

    v_tickets = [
        v_single_swl, v_single_ash, v_single_ka2,
        v_month_swl, v_month_ash, v_month_ka2, v_month_ahl_20_21,
        v_season_swl, v_season_ash, v_season_ka2, v_season_ahl_20_21,
        v_day_ahl_20_21
    ]

    ticket_type_ap = AttributeProduct.objects.create(attribute=ticket_type_attr, product_type=product_type)
    leagues_ap = AttributeProduct.objects.create(attribute=leagues_attribute, product_type=product_type)
    teams_ap = AttributeProduct.objects.create(attribute=teams_attribute, product_type=product_type)

    ticket_type_av = AttributeVariant.objects.create(attribute=ticket_type_attr, product_type=product_type)
    leagues_av = AttributeVariant.objects.create(attribute=leagues_attribute, product_type=product_type)
    teams_av = AttributeVariant.objects.create(attribute=teams_attribute, product_type=product_type)

    # Single
    assign_product_attr_value(single_swl, ticket_type_ap, type_single)
    assign_product_attr_value(single_swl, teams_ap, team_swl)
    assign_product_attr_value(single_ka2, ticket_type_ap, type_single)
    assign_product_attr_value(single_ka2, teams_ap, team_ka2)
    assign_product_attr_value(single_ash, ticket_type_ap, type_single)
    assign_product_attr_value(single_ash, teams_ap, team_ash)

    # Day
    assign_product_attr_value(day_ahl_20_21, ticket_type_ap, type_day)
    assign_product_attr_value(day_ahl_20_21, leagues_ap, league_20_21)

    # Month
    assign_product_attr_value(month_ahl_20_21, ticket_type_ap, type_month)
    assign_product_attr_value(month_ahl_20_21, leagues_ap, league_20_21)
    assign_product_attr_value(month_ahl_20_21, teams_ap, team_all)
    assign_product_attr_value(month_swl, ticket_type_ap, type_month)
    assign_product_attr_value(month_swl, leagues_ap, league_20_21)
    assign_product_attr_value(month_swl, teams_ap, team_swl)
    assign_product_attr_value(month_ka2, ticket_type_ap, type_month)
    assign_product_attr_value(month_ka2, leagues_ap, league_20_21)
    assign_product_attr_value(month_ka2, teams_ap, team_ka2)
    assign_product_attr_value(month_ash, ticket_type_ap, type_month)
    assign_product_attr_value(month_ash, leagues_ap, league_20_21)
    assign_product_attr_value(month_ash, teams_ap, team_ash)

    # Season
    assign_product_attr_value(season_ahl_20_21, ticket_type_ap, type_season)
    assign_product_attr_value(season_ahl_20_21, teams_ap, team_all)
    assign_product_attr_value(season_swl, ticket_type_ap, type_season)
    assign_product_attr_value(season_swl, teams_ap, team_swl)
    assign_product_attr_value(season_ka2, ticket_type_ap, type_season)
    assign_product_attr_value(season_ka2, teams_ap, team_ka2)
    assign_product_attr_value(season_ash, ticket_type_ap, type_season)
    assign_product_attr_value(season_ash, teams_ap, team_ash)

    # VARIANTS:
    assign_variant_attr_value(v_single_swl, ticket_type_av, type_single)
    assign_variant_attr_value(v_single_swl, teams_av, team_swl)
    assign_variant_attr_value(v_single_ka2, ticket_type_av, type_single)
    assign_variant_attr_value(v_single_ka2, teams_av, team_ka2)
    assign_variant_attr_value(v_single_ash, ticket_type_av, type_single)
    assign_variant_attr_value(v_single_ash, teams_av, team_ash)

    # Day
    assign_variant_attr_value(v_day_ahl_20_21, ticket_type_av, type_day)
    assign_variant_attr_value(v_day_ahl_20_21, leagues_av, league_20_21)

    # Month
    assign_variant_attr_value(v_month_ahl_20_21, ticket_type_av, type_month)
    assign_variant_attr_value(v_month_ahl_20_21, leagues_av, league_20_21)
    assign_variant_attr_value(v_month_ahl_20_21, teams_av, team_all)
    assign_variant_attr_value(v_month_swl, ticket_type_av, type_month)
    assign_variant_attr_value(v_month_swl, leagues_av, league_20_21)
    assign_variant_attr_value(v_month_swl, teams_av, team_swl)
    assign_variant_attr_value(v_month_ka2, ticket_type_av, type_month)
    assign_variant_attr_value(v_month_ka2, leagues_av, league_20_21)
    assign_variant_attr_value(v_month_ka2, teams_av, team_ka2)
    assign_variant_attr_value(v_month_ash, ticket_type_av, type_month)
    assign_variant_attr_value(v_month_ash, leagues_av, league_20_21)
    assign_variant_attr_value(v_month_ash, teams_av, team_ash)

    # Season
    assign_variant_attr_value(v_season_ahl_20_21, ticket_type_av, type_season)
    assign_variant_attr_value(v_season_ahl_20_21, teams_av, team_all)
    assign_variant_attr_value(v_season_swl, ticket_type_av, type_season)
    assign_variant_attr_value(v_season_swl, teams_av, team_swl)
    assign_variant_attr_value(v_season_ka2, ticket_type_av, type_season)
    assign_variant_attr_value(v_season_ka2, teams_av, team_ka2)
    assign_variant_attr_value(v_season_ash, ticket_type_av, type_season)
    assign_variant_attr_value(v_season_ash, teams_av, team_ash)

    return tickets


def create_product_with_variant(slug, category, product_type, channel):
    product = Product.objects.create(
        name=slug, slug=slug, category=category, product_type=product_type,
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku=str(uuid.uuid4()).replace("-", ""),
        track_inventory=False,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel,
        is_published=True,
        visible_in_listings=True,
        discounted_price_amount=Decimal(5),
        available_for_purchase=datetime.date(2002, 1, 1),
        publication_date=datetime.date(2002, 1, 1),
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel,
        price_amount=Decimal(5),
        currency=channel.currency_code,
    )
    return product, variant


def assign_product_attr_value(product, attribute_product, attribute_value):
    assigned_product_attribute = AssignedProductAttribute.objects.create(
        product=product,
        assignment=attribute_product
    )
    AssignedProductAttributeValue.objects.create(
        value=attribute_value,
        assignment=assigned_product_attribute
    )


def assign_variant_attr_value(variant, attribute_variant, attribute_value):
    assigned_variant_attribute = AssignedVariantAttribute.objects.create(
        variant=variant,
        assignment=attribute_variant
    )
    AssignedVariantAttributeValue.objects.create(
        value=attribute_value,
        assignment=assigned_variant_attribute
    )

