import pytest
from django.core.exceptions import ValidationError

from .....graphql.tests.utils import get_graphql_content, \
    assert_graphql_error_with_message
from .....product.models import Product

QUERY_TICKET_PRODUCTS_WITH_FILTERING = """
    query (
        $channel: String,
        $filter: TicketProductFilterInput
    ){
        ticketProducts (
            first: 25,
            channel: $channel,
            filter: $filter
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "filter_by, products_count",
    [
        ({
            "singleTeams": ["swl"],
            "teams": ["swl"],
            "leagues": ["ahl-20-21"],
         }, 4),
        ({
            "singleTeams": ["swl"],
            "teams": ["all-teams"],
            "leagues": ["ahl-20-21"],
         }, 4),
        ({
            "singleTeams": ["swl"],
            "teams": ["swl", "ash", "ka2", "all-teams"],
            "leagues": ["ahl-20-21"],
         }, 10),
        ({
            "singleTeams": ["swl", "ka2", "ash"],
            "teams": ["swl", "ash", "ka2", "all-teams"],
            "leagues": ["ahl-20-21"],
         }, 12),
        ({
            "singleTeams": ["swl", "ka2", "ash"],
            "teams": ["swl", "ash", "ka2"],
            "leagues": ["ahl-20-21"],
         }, 10),
        ({
            "singleTeams": ["swl"],
            "teams": ["all-teams"],
            "leagues": ["ahl-20-21"],
        }, 4),
        ({
            "singleTeams": ["swl", "ash", "rbs", "any"],
            "teams": ["ash", "all-teams"],
            "leagues": ["ahl-20-21"],
        }, 7),
    ],
)
def test_ticket_product_query_with_filters(
        filter_by,
        products_count,
        user_api_client,
        channel_EUR,
        ticket_products_for_filtering,
    ):
    # when
    response = user_api_client.post_graphql(
        QUERY_TICKET_PRODUCTS_WITH_FILTERING,
        variables={
            "filter": filter_by,
            "channel": channel_EUR.slug
        },
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["ticketProducts"]["edges"]
    assert len(products_nodes) == products_count


@pytest.mark.parametrize(
    "filter_by,key",
    [
        ({
             "teams": ["swl"],
             "leagues": ["ahl-20-21"],
        }, "single_teams"),
        ({
            "singleTeams": ["swl"],
            "leagues": ["ahl-20-21"],
        }, "teams"),
        ({
            "singleTeams": ["swl"],
            "teams": ["swl"],
        }, "leagues")
    ],
)
def test_ticket_product_query_with_invalid_filters(
        filter_by,
        key,
        user_api_client,
        channel_EUR,
        ticket_products_for_filtering,
    ):
    response = user_api_client.post_graphql(
        QUERY_TICKET_PRODUCTS_WITH_FILTERING,
        variables={
            "filter": filter_by,
            "channel": channel_EUR.slug,
        },
    )
    assert_graphql_error_with_message(response, "Missing filter attribute: " + key)

