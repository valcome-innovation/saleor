import datetime
import uuid
import warnings
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django_countries.fields import Country
from measurement.measures import Weight
from prices import Money

from ....account.models import User
from ....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....checkout import AddressType, calculations
from ....checkout.checkout_cleaner import (
    clean_checkout_payment,
    clean_checkout_shipping,
)
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    get_delivery_method_info,
)
from ....checkout.models import Checkout
from ....checkout.utils import add_variant_to_checkout, calculate_checkout_quantity
from ....core.payments import PaymentInterface
from ....payment import TransactionKind
from ....payment.interface import GatewayResponse
from ....plugins.base_plugin import ExcludedShippingMethod
from ....plugins.manager import get_plugins_manager
from ....plugins.tests.sample_plugins import ActiveDummyPaymentGateway
from ....product.models import ProductChannelListing, ProductVariant
from ....shipping import models as shipping_models
from ....shipping.models import ShippingMethodTranslation
from ....shipping.utils import convert_to_shipping_method_data
from ....tests.utils import dummy_editorjs
from ....warehouse.models import Stock
from ...shipping.enums import ShippingMethodTypeEnum
from ...tests.utils import assert_no_permission, get_graphql_content
from ..mutations import (
    clean_shipping_method,
    update_checkout_shipping_method_if_invalid,
)


def test_clean_shipping_method_after_shipping_address_changes_stay_the_same(
    checkout_with_single_item, address, shipping_method, other_shipping_method
):
    """Ensure the current shipping method applies to new address.

    If it does, then it doesn't need to be changed.
    """

    checkout = checkout_with_single_item
    checkout.shipping_address = address

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    is_valid_method = clean_shipping_method(
        checkout_info,
        lines,
        convert_to_shipping_method_data(
            shipping_method,
            shipping_method.channel_listings.get(),
        ),
    )
    assert is_valid_method is True


def test_clean_shipping_method_does_nothing_if_no_shipping_method(
    checkout_with_single_item, address, other_shipping_method
):
    """If no shipping method was selected, it shouldn't return an error."""

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    is_valid_method = clean_shipping_method(checkout_info, lines, None)
    assert is_valid_method is True


def test_update_checkout_shipping_method_if_invalid(
    checkout_with_single_item,
    address,
    shipping_method,
    other_shipping_method,
    shipping_zone_without_countries,
):
    # If the shipping method is invalid, it should be removed.

    checkout = checkout_with_single_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method

    shipping_method.shipping_zone = shipping_zone_without_countries
    shipping_method.save(update_fields=["shipping_zone"])

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    update_checkout_shipping_method_if_invalid(checkout_info, lines)

    assert checkout.shipping_method is None
    assert checkout_info.delivery_method_info.delivery_method is None

    # Ensure the checkout's shipping method was saved
    checkout.refresh_from_db(fields=["shipping_method"])
    assert checkout.shipping_method is None


MUTATION_CHECKOUT_CREATE = """
    mutation createCheckout($checkoutInput: CheckoutCreateInput!) {
      checkoutCreate(input: $checkoutInput) {
        checkout {
          id
          token
          email
          quantity
          lines {
            quantity
          }
        }
        errors {
          field
          message
          code
          variants
          addressType
        }
      }
    }
"""


@mock.patch("saleor.plugins.webhook.plugin._get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_for_event.delay")
def test_checkout_create_triggers_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    user_api_client,
    stock,
    graphql_address_data,
    settings,
    channel_USD,
):
    """Create checkout object using GraphQL API."""
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": user_api_client.user.email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    get_graphql_content(response)

    assert mocked_webhook_trigger.called


def test_checkout_create_with_default_channel(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    quantity = 1
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": quantity, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    lines, _ = fetch_checkout_lines(new_checkout)
    assert new_checkout.channel == channel_USD
    assert calculate_checkout_quantity(lines) == quantity

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_channel(
    api_client, stock, graphql_address_data, channel_USD
):
    channel = channel_USD
    channel.is_active = False
    channel.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name


def test_checkout_create_with_zero_quantity(
    api_client, stock, graphql_address_data, channel_USD
):

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 0, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "quantity"
    assert error["code"] == CheckoutErrorCode.ZERO_QUANTITY.name


def test_checkout_create_with_unavailable_variant(
    api_client, stock, graphql_address_data, channel_USD
):

    variant = stock.product_variant
    variant.channel_listings.filter(channel=channel_USD).update(price_amount=None)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert error["variants"] == [variant_id]


def test_checkout_create_with_malicious_variant_id(
    api_client, stock, graphql_address_data, channel_USD
):

    variant = stock.product_variant
    variant.channel_listings.filter(channel=channel_USD).update(price_amount=None)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variant_id = (
        "UHJvZHVjdFZhcmlhbnQ6NDkxMyd8fERCTVNfUElQRS5SRUNFSVZFX01FU1N"
        "BR0UoQ0hSKDk4KXx8Q0hSKDk4KXx8Q0hSKDk4KSwxNSl8fCc="
    )
    # This string translates to
    # ProductVariant:4913'||DBMS_PIPE.RECEIVE_MESSAGE(CHR(98)||CHR(98)||CHR(98),15)||'

    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "variantId"
    assert error["code"] == "GRAPHQL_ERROR"


def test_checkout_create_with_inactive_default_channel(
    api_client, stock, graphql_address_data, channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    assert not Checkout.objects.exists()
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()

    assert new_checkout.channel == channel_USD

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_and_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    channel_PLN.is_active = False
    channel_PLN.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    assert not Checkout.objects.exists()
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
        get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()

    assert new_checkout.channel == channel_USD

    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_checkout_create_with_inactive_and_two_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN, other_channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()

    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_many_active_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_many_inactive_default_channel(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    channel_USD.is_active = False
    channel_USD.save()
    channel_PLN.is_active = False
    channel_PLN.save()
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_multiple_channel_without_channel_slug(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.MISSING_CHANNEL_SLUG.name


def test_checkout_create_with_multiple_channel_with_channel_slug(
    api_client, stock, graphql_address_data, channel_USD, channel_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    assert new_checkout.channel == channel_USD
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1


def test_checkout_create_with_existing_checkout_in_other_channel(
    user_api_client, stock, graphql_address_data, channel_USD, user_checkout_PLN
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    old_checkout = Checkout.objects.first()

    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    content = get_graphql_content(response)["data"]["checkoutCreate"]

    checkout_data = content["checkout"]
    assert checkout_data["token"] != str(old_checkout.token)


def test_checkout_create_with_inactive_channel_slug(
    api_client, stock, graphql_address_data, channel_USD
):
    channel = channel_USD
    channel.is_active = False
    channel.save()
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    error = get_graphql_content(response)["data"]["checkoutCreate"]["errors"][0]

    assert error["field"] == "channel"
    assert error["code"] == CheckoutErrorCode.CHANNEL_INACTIVE.name


def test_checkout_create(api_client, stock, graphql_address_data, channel_USD):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is not None
    assert new_checkout.shipping_address.first_name == shipping_address["firstName"]
    assert new_checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        new_checkout.shipping_address.street_address_1
        == shipping_address["streetAddress1"]
    )
    assert (
        new_checkout.shipping_address.street_address_2
        == shipping_address["streetAddress2"]
    )
    assert new_checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert new_checkout.shipping_address.country == shipping_address["country"]
    assert new_checkout.shipping_address.city == shipping_address["city"].upper()


def test_checkout_create_with_invalid_channel_slug(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    invalid_slug = "invalid-slug"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": invalid_slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]
    error = content["errors"][0]

    assert error["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert error["field"] == "channel"


def test_checkout_create_no_channel_shipping_zones(
    api_client, stock, graphql_address_data, channel_USD
):
    """Create checkout object using GraphQL API."""
    channel_USD.shipping_zones.clear()
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is None
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_create_multiple_warehouse(
    api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 4, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 4


def test_checkout_create_with_null_as_addresses(api_client, stock, channel_USD):
    """Create checkout object using GraphQL API."""
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": None,
            "billingAddress": None,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is None
    assert new_checkout.billing_address is None


def test_checkout_create_with_variant_without_inventory_tracking(
    api_client, variant_without_inventory_tracking, channel_USD
):
    """Create checkout object using GraphQL API."""
    variant = variant_without_inventory_tracking
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": None,
            "billingAddress": None,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    assert new_checkout.lines.count() == 1
    checkout_line = new_checkout.lines.first()
    assert checkout_line.variant == variant
    assert checkout_line.quantity == 1
    assert new_checkout.shipping_address is None
    assert new_checkout.billing_address is None


@pytest.mark.parametrize(
    "quantity, expected_error_message, error_code",
    (
        (
            -1,
            "The quantity should be higher than zero.",
            CheckoutErrorCode.ZERO_QUANTITY,
        ),
        (
            51,
            "Cannot add more than 50 times this item.",
            CheckoutErrorCode.QUANTITY_GREATER_THAN_LIMIT,
        ),
    ),
)
def test_checkout_create_cannot_add_invalid_quantities(
    api_client,
    stock,
    graphql_address_data,
    quantity,
    channel_USD,
    expected_error_message,
    error_code,
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": quantity, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]
    assert content["errors"]
    assert content["errors"] == [
        {
            "field": "quantity",
            "message": expected_error_message,
            "code": error_code.name,
            "variants": None,
            "addressType": None,
        }
    ]


def test_checkout_create_reuse_checkout(checkout, user_api_client, stock):
    # assign user to the checkout
    checkout.user = user_api_client.user
    checkout.save()
    variant = stock.product_variant

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "channel": checkout.channel.slug,
        },
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)["data"]["checkoutCreate"]

    checkout_data = content["checkout"]
    assert checkout_data["token"] != str(checkout.token)

    assert len(checkout_data["lines"]) == 1


def test_checkout_create_required_email(api_client, stock, channel_USD):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "",
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    errors = content["data"]["checkoutCreate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutCreate"]["errors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name


def test_checkout_create_required_country_shipping_address(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    del shipping_address["country"]
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["errors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_errors[0]["addressType"] == AddressType.SHIPPING.upper()


def test_checkout_create_required_country_billing_address(
    api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    billing_address = graphql_address_data
    del billing_address["country"]
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": "test@example.com",
            "billingAddress": billing_address,
            "channel": channel_USD.slug,
        }
    }

    response = api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)

    checkout_errors = content["data"]["checkoutCreate"]["errors"]
    assert checkout_errors[0]["field"] == "country"
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_errors[0]["addressType"] == AddressType.BILLING.upper()


def test_checkout_create_default_email_for_logged_in_customer(
    user_api_client, stock, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "channel": channel_USD.slug,
        }
    }
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    customer = user_api_client.user
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["email"] == str(customer.email)
    assert new_checkout.user.id == customer.id
    assert new_checkout.email == customer.email


def test_checkout_create_logged_in_customer(user_api_client, stock, channel_USD):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "email": user_api_client.user.email,
            "lines": [{"quantity": 1, "variantId": variant_id}],
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    customer = user_api_client.user
    assert customer.id == checkout_user.id
    assert customer.default_shipping_address_id != new_checkout.shipping_address_id
    assert (
        customer.default_shipping_address.as_data()
        == new_checkout.shipping_address.as_data()
    )
    assert customer.default_billing_address_id != new_checkout.billing_address_id
    assert (
        customer.default_billing_address.as_data()
        == new_checkout.billing_address.as_data()
    )
    assert customer.email == new_checkout.email


def test_checkout_create_logged_in_customer_custom_email(
    user_api_client, stock, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    customer = user_api_client.user
    custom_email = "custom@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": custom_email,
        }
    }
    assert not Checkout.objects.exists()
    assert not custom_email == customer.email
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    assert customer.id == checkout_user.id
    assert new_checkout.email == custom_email


def test_checkout_create_logged_in_customer_custom_addresses(
    user_api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    shipping_address = graphql_address_data
    billing_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "email": user_api_client.user.email,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "shippingAddress": shipping_address,
            "billingAddress": billing_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    new_checkout = Checkout.objects.first()
    assert new_checkout is not None
    checkout_data = content["data"]["checkoutCreate"]["checkout"]
    assert checkout_data["token"] == str(new_checkout.token)
    checkout_user = new_checkout.user
    customer = user_api_client.user
    assert customer.id == checkout_user.id
    assert not (
        customer.default_shipping_address_id == new_checkout.shipping_address_id
    )
    assert not (customer.default_billing_address_id == new_checkout.billing_address_id)
    assert new_checkout.shipping_address.first_name == shipping_address["firstName"]
    assert new_checkout.billing_address.first_name == billing_address["firstName"]


def test_checkout_create_check_lines_quantity_multiple_warehouse(
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 7 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_when_all_stocks_exceeded(
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "channel": channel_USD.slug,
        }
    }

    # make stocks exceeded and assert
    variant.stocks.update(quantity=-99)
    for stock in variant.stocks.all():
        assert stock.quantity == -99

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 0 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_when_one_stock_exceeded(
    user_api_client, variant_with_many_stocks, graphql_address_data, channel_USD
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": "test@example.com",
            "shippingAddress": graphql_address_data,
            "channel": channel_USD.slug,
        }
    }

    # make first stock exceeded
    stock = variant.stocks.first()
    stock.quantity = -1
    stock.save()

    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 2 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_create_sets_country_from_shipping_address_country(
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
    channel_USD,
):
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = 10001
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    content["data"]["checkoutCreate"]
    checkout = Checkout.objects.first()
    assert checkout.country == "US"


def test_checkout_create_sets_country_when_no_shipping_address_is_given(
    api_client, variant_with_many_stocks_different_shipping_zones, channel_USD
):
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
        }
    }
    assert not Checkout.objects.exists()

    # should set channel's default_country
    api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    checkout = Checkout.objects.first()
    assert checkout.country == channel_USD.default_country


@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_create_check_lines_quantity_for_zone_insufficient_stocks(
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
    channel_USD,
):
    """Check if insufficient stock exception will be raised.
    If item from checkout will not have enough quantity in correct shipping zone for
    shipping address INSUFICIENT_STOCK checkout error should be raised."""
    variant = variant_with_many_stocks_different_shipping_zones
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = 10001
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 1, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert not data["checkout"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_create_check_lines_quantity(
    user_api_client, stock, graphql_address_data, channel_USD
):
    variant = stock.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 16, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]
    assert data["errors"][0]["message"] == (
        "Could not add items SKU_A. Only 15 remaining in stock."
    )
    assert data["errors"][0]["field"] == "quantity"


def test_checkout_create_unavailable_for_purchase_product(
    user_api_client, stock, graphql_address_data, channel_USD
):
    # given
    variant = stock.product_variant
    product = variant.product

    product.channel_listings.update(available_for_purchase=None)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 10, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["variants"] == [variant_id]


def test_checkout_create_available_for_purchase_from_tomorrow_product(
    user_api_client, stock, graphql_address_data, channel_USD
):
    # given
    variant = stock.product_variant
    product = variant.product

    product.channel_listings.update(
        available_for_purchase=datetime.date.today() + datetime.timedelta(days=1)
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    test_email = "test@example.com"
    shipping_address = graphql_address_data
    variables = {
        "checkoutInput": {
            "lines": [{"quantity": 10, "variantId": variant_id}],
            "email": test_email,
            "shippingAddress": shipping_address,
            "channel": channel_USD.slug,
        }
    }
    assert not Checkout.objects.exists()

    # when
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_CREATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name
    assert errors[0]["variants"] == [variant_id]


@pytest.fixture
def expected_dummy_gateway():
    return {
        "id": "mirumee.payments.dummy",
        "name": "Dummy",
        "config": [{"field": "store_customer_card", "value": "false"}],
        "currencies": ["USD", "PLN"],
    }


GET_CHECKOUT_PAYMENTS_QUERY = """
query getCheckoutPayments($token: UUID!) {
    checkout(token: $token) {
        availablePaymentGateways {
            id
            name
            config {
                field
                value
            }
            currencies
        }
    }
}
"""


def test_checkout_available_payment_gateways(
    api_client,
    checkout_with_item,
    expected_dummy_gateway,
):
    query = GET_CHECKOUT_PAYMENTS_QUERY
    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availablePaymentGateways"] == [
        expected_dummy_gateway,
    ]


def test_checkout_available_payment_gateways_currency_specified_USD(
    api_client,
    checkout_with_item,
    expected_dummy_gateway,
    sample_gateway,
):
    checkout_with_item.currency = "USD"
    checkout_with_item.save(update_fields=["currency"])

    query = GET_CHECKOUT_PAYMENTS_QUERY

    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert {gateway["id"] for gateway in data["availablePaymentGateways"]} == {
        expected_dummy_gateway["id"],
        ActiveDummyPaymentGateway.PLUGIN_ID,
    }


def test_checkout_available_payment_gateways_currency_specified_EUR(
    api_client, checkout_with_item, expected_dummy_gateway, sample_gateway
):
    checkout_with_item.currency = "EUR"
    checkout_with_item.save(update_fields=["currency"])

    query = GET_CHECKOUT_PAYMENTS_QUERY

    variables = {"token": str(checkout_with_item.token)}
    response = api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert (
        data["availablePaymentGateways"][0]["id"] == ActiveDummyPaymentGateway.PLUGIN_ID
    )


GET_CHECKOUT_SELECTED_SHIPPING_METHOD = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        shippingMethod {
            id
            type
            name
            description
            price {
                amount
            }
            translation(languageCode: PL) {
                name
                description
            }
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            minimumOrderWeight {
               unit
               value
            }
            maximumOrderWeight {
               unit
               value
            }
            message
            active
            minimumDeliveryDays
            maximumDeliveryDays
            metadata {
                key
                value
            }
        }
    }
}
"""


def test_checkout_selected_shipping_method(
    api_client, checkout_with_item, address, shipping_zone
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    min_weight = 0
    shipping_method.minimum_order_weight = Weight(oz=min_weight)
    max_weight = 10
    shipping_method.maximum_order_weight = Weight(kg=max_weight)
    metadata_key = "md key"
    metadata_value = "md value"
    raw_description = "this is descr"
    description = dummy_editorjs(raw_description)
    shipping_method.description = description
    shipping_method.store_value_in_metadata({metadata_key: metadata_value})
    shipping_method.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save()

    # when
    query = GET_CHECKOUT_SELECTED_SHIPPING_METHOD
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data["shippingMethod"]["id"] == (
        graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    )
    assert data["shippingMethod"]["name"] == shipping_method.name
    assert raw_description in data["shippingMethod"]["description"]
    assert data["shippingMethod"]["type"] == ShippingMethodTypeEnum.PRICE.name
    assert data["shippingMethod"]["active"]
    assert data["shippingMethod"]["message"] == ""
    assert (
        data["shippingMethod"]["minimumDeliveryDays"]
        == shipping_method.minimum_delivery_days
    )
    assert (
        data["shippingMethod"]["maximumDeliveryDays"]
        == shipping_method.maximum_delivery_days
    )
    assert data["shippingMethod"]["minimumOrderWeight"]["unit"] == "KG"
    assert data["shippingMethod"]["minimumOrderWeight"]["value"] == min_weight
    assert data["shippingMethod"]["maximumOrderWeight"]["unit"] == "KG"
    assert data["shippingMethod"]["maximumOrderWeight"]["value"] == max_weight
    assert data["shippingMethod"]["metadata"][0]["key"] == metadata_key
    assert data["shippingMethod"]["metadata"][0]["value"] == metadata_value
    assert data["shippingMethod"]["translation"]["name"] == translated_name


GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        %s {
            id
            type
            name
            description
            price {
                amount
            }
            translation(languageCode: PL) {
                name
                description
            }
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            minimumOrderWeight {
               unit
               value
            }
            maximumOrderWeight {
               unit
               value
            }
            message
            active
            minimumDeliveryDays
            maximumDeliveryDays
            metadata {
                key
                value
            }
        }
    }
}
"""

GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS = (
    GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE % "availableShippingMethods"
)


@pytest.mark.parametrize("field", ["availableShippingMethods", "shippingMethods"])
def test_checkout_available_shipping_methods(
    api_client, checkout_with_item, address, shipping_zone, field
):
    # given
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    min_weight = 0
    shipping_method.minimum_order_weight = Weight(oz=min_weight)
    max_weight = 10
    shipping_method.maximum_order_weight = Weight(kg=max_weight)
    metadata_key = "md key"
    metadata_value = "md value"
    raw_description = "this is descr"
    description = dummy_editorjs(raw_description)
    shipping_method.description = description
    shipping_method.store_value_in_metadata({metadata_key: metadata_value})
    shipping_method.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )

    # when
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS_TEMPLATE % field
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    # then
    assert data[field][0]["id"] == (
        graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    )
    assert data[field][0]["name"] == shipping_method.name
    assert raw_description in data[field][0]["description"]
    assert data[field][0]["type"] == ShippingMethodTypeEnum.PRICE.name
    assert data[field][0]["active"]
    assert data[field][0]["message"] == ""
    assert (
        data[field][0]["minimumDeliveryDays"] == shipping_method.minimum_delivery_days
    )
    assert (
        data[field][0]["maximumDeliveryDays"] == shipping_method.maximum_delivery_days
    )
    assert data[field][0]["minimumOrderWeight"]["unit"] == "KG"
    assert data[field][0]["minimumOrderWeight"]["value"] == min_weight
    assert data[field][0]["maximumOrderWeight"]["unit"] == "KG"
    assert data[field][0]["maximumOrderWeight"]["value"] == max_weight
    assert data[field][0]["metadata"][0]["key"] == metadata_key
    assert data[field][0]["metadata"][0]["value"] == metadata_value
    assert data[field][0]["translation"]["name"] == translated_name


@pytest.mark.parametrize("minimum_order_weight_value", [0, 2, None])
def test_checkout_available_shipping_methods_with_weight_based_shipping_method(
    api_client,
    checkout_with_item,
    address,
    shipping_method_weight_based,
    minimum_order_weight_value,
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    shipping_method = shipping_method_weight_based
    if minimum_order_weight_value is not None:
        weight = Weight(kg=minimum_order_weight_value)
        shipping_method.minimum_order_weight = weight
        variant = checkout_with_item.lines.first().variant
        variant.weight = weight
        variant.save(update_fields=["weight"])
    else:
        shipping_method.minimum_order_weight = minimum_order_weight_value

    shipping_method.save(update_fields=["minimum_order_weight"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name in shipping_methods


def test_checkout_available_shipping_methods_weight_method_with_higher_minimal_weigh(
    api_client, checkout_with_item, address, shipping_method_weight_based
):
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    shipping_method = shipping_method_weight_based
    weight_value = 5
    shipping_method.minimum_order_weight = Weight(kg=weight_value)
    shipping_method.save(update_fields=["minimum_order_weight"])

    variants = []
    for line in checkout_with_item.lines.all():
        variant = line.variant
        variant.weight = Weight(kg=1)
        variants.append(variant)
    ProductVariant.objects.bulk_update(variants, ["weight"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name not in shipping_methods


def test_checkout_shipping_methods_with_price_based_shipping_method_and_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
):
    """Ensure that price based shipping method is not returned when
    checkout with discounts subtotal is lower than minimal order price."""
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    checkout_with_item.discount_amount = Decimal(5.0)
    checkout_with_item.save(update_fields=["shipping_address", "discount_amount"])

    shipping_method.name = "Price based"
    shipping_method.save(update_fields=["name"])

    shipping_channel_listing = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    )
    shipping_channel_listing.minimum_order_price_amount = subtotal.gross.amount - 1
    shipping_channel_listing.save(update_fields=["minimum_order_price_amount"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name not in shipping_methods


def test_checkout_shipping_methods_with_price_based_shipping_and_shipping_discount(
    api_client,
    checkout_with_item,
    address,
    shipping_method,
    voucher_shipping_type,
):
    """Ensure that price based shipping method is returned when checkout
    has discount on shipping."""
    checkout_with_item.shipping_address = address
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )

    checkout_with_item.discount_amount = Decimal(5.0)
    checkout_with_item.voucher_code = voucher_shipping_type.code
    checkout_with_item.save(
        update_fields=["shipping_address", "discount_amount", "voucher_code"]
    )

    shipping_method.name = "Price based"
    shipping_method.save(update_fields=["name"])

    shipping_channel_listing = shipping_method.channel_listings.get(
        channel=checkout_with_item.channel
    )
    shipping_channel_listing.minimum_order_price_amount = subtotal.gross.amount - 1
    shipping_channel_listing.save(update_fields=["minimum_order_price_amount"])

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    shipping_methods = [method["name"] for method in data["availableShippingMethods"]]
    assert shipping_method.name in shipping_methods


def test_checkout_available_shipping_methods_shipping_zone_without_channels(
    api_client, checkout_with_item, address, shipping_zone
):
    shipping_zone.channels.clear()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert len(data["availableShippingMethods"]) == 0


def test_checkout_available_shipping_methods_excluded_postal_codes(
    api_client, checkout_with_item, address, shipping_zone
):
    address.country = Country("GB")
    address.postal_code = "BH16 7HF"
    address.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.postal_code_rules.create(start="BH16 7HA", end="BH16 7HG")

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["availableShippingMethods"] == []


def test_checkout_available_shipping_methods_with_price_displayed(
    api_client,
    checkout_with_item,
    address,
    shipping_zone,
):
    shipping_method = shipping_zone.shipping_methods.first()
    method_listing = shipping_method.channel_listings.get(
        channel_id=checkout_with_item.channel_id
    )
    method_listing.minimum_order_price = Money(
        Decimal("5.37"), checkout_with_item.currency
    )
    method_listing.maximum_order_price = Money(
        Decimal("115.73"), checkout_with_item.currency
    )
    method_listing.save()
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    translated_name = "Dostawa ekspresowa"
    ShippingMethodTranslation.objects.create(
        language_code="pl", shipping_method=shipping_method, name=translated_name
    )

    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"][0]["name"] == shipping_method.name
    assert data["availableShippingMethods"][0]["price"]["amount"] == float(
        method_listing.price.amount
    )
    assert data["availableShippingMethods"][0]["minimumOrderPrice"]["amount"] == float(
        method_listing.minimum_order_price.amount
    )
    assert data["availableShippingMethods"][0]["maximumOrderPrice"]["amount"] == float(
        method_listing.maximum_order_price.amount
    )
    assert data["availableShippingMethods"][0]["name"] == "DHL"
    assert data["availableShippingMethods"][0]["translation"]["name"] == translated_name


def test_checkout_no_available_shipping_methods_without_address(
    api_client, checkout_with_item
):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS
    variables = {"token": checkout_with_item.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


def test_checkout_no_available_shipping_methods_without_lines(api_client, checkout):
    query = GET_CHECKOUT_AVAILABLE_SHIPPING_METHODS

    variables = {"token": checkout.token}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]

    assert data["availableShippingMethods"] == []


def test_create_checkout_with_unpublished_product(
    user_api_client, checkout_with_item, stock, channel_USD
):
    variant = stock.product_variant
    product = variant.product
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    query = """
            mutation CreateCheckout($checkoutInput: CheckoutCreateInput!) {
              checkoutCreate(input: $checkoutInput) {
                errors {
                  code
                  message
                }
                checkout {
                  id
                }
              }
            }
        """
    variables = {
        "checkoutInput": {
            "channel": channel_USD.slug,
            "email": "test@example.com",
            "lines": [{"variantId": variant_id, "quantity": 1}],
        }
    }
    response = get_graphql_content(user_api_client.post_graphql(query, variables))
    error = response["data"]["checkoutCreate"]["errors"][0]
    assert error["code"] == CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.name


def test_checkout_customer_attach(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = """
        mutation checkoutCustomerAttach($token: UUID) {
            checkoutCustomerAttach(token: $token) {
                checkout {
                    token
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"token": checkout.token, "customerId": customer_id}

    # Mutation should fail for unauthenticated customers
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = """
        mutation checkoutCustomerAttach($token: UUID, $customerId: ID) {
            checkoutCustomerAttach(token: $token, customerId: $customerId) {
                checkout {
                    token
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"token": checkout.token, "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app_without_permission(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = """
        mutation checkoutCustomerAttach($token: UUID, $customerId: ID) {
            checkoutCustomerAttach(token: $token, customerId: $customerId) {
                checkout {
                    token
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"token": checkout.token, "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    assert_no_permission(response)


def test_checkout_customer_attach_user_to_checkout_with_user(
    user_api_client, customer_user, user_checkout, address
):
    checkout = user_checkout

    query = """
    mutation checkoutCustomerAttach($checkoutId: ID, $token: UUID) {
        checkoutCustomerAttach(checkoutId: $checkoutId, token: $token) {
            checkout {
                token
            }
            errors {
                field
                message
                code
            }
        }
    }
"""

    default_address = address.get_copy()
    second_user = User.objects.create_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Test2",
        last_name="Tested",
    )

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", second_user.pk)
    variables = {"checkoutId": checkout_id, "customerId": customer_id}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


MUTATION_CHECKOUT_CUSTOMER_DETACH = """
    mutation checkoutCustomerDetach($token: UUID) {
        checkoutCustomerDetach(token: $token) {
            checkout {
                token
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_checkout_customer_detach(user_api_client, checkout_with_item, customer_user):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"token": checkout.token}

    # Mutation should succeed if the user owns this checkout.
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change

    # Mutation should fail when user calling it doesn't own the checkout.
    other_user = User.objects.create_user("othercustomer@example.com", "password")
    checkout.user = other_user
    checkout.save()
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH, variables
    )
    assert_no_permission(response)


def test_checkout_customer_detach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"token": checkout.token}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_DETACH,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerDetach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user is None
    assert checkout.last_change != previous_last_change


def test_checkout_customer_detach_by_app_without_permissions(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    previous_last_change = checkout.last_change

    variables = {"token": checkout.token}

    # Mutation should succeed if the user owns this checkout.
    response = app_api_client.post_graphql(MUTATION_CHECKOUT_CUSTOMER_DETACH, variables)

    assert_no_permission(response)
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $token: UUID, $shippingAddress: AddressInput!) {
        checkoutShippingAddressUpdate(
                token: $token, shippingAddress: $shippingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field
                message
                code
            }
        }
    }"""


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
def test_checkout_shipping_address_update(
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {"token": checkout_with_item.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address is not None
    assert checkout.shipping_address.first_name == shipping_address["firstName"]
    assert checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        checkout.shipping_address.street_address_1 == shipping_address["streetAddress1"]
    )
    assert (
        checkout.shipping_address.street_address_2 == shipping_address["streetAddress2"]
    )
    assert checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert checkout.shipping_address.country == shipping_address["country"]
    assert checkout.shipping_address.city == shipping_address["city"].upper()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_changes_checkout_country(
    mocked_update_shipping_method,
    user_api_client,
    channel_USD,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address is not None
    assert checkout.shipping_address.first_name == shipping_address["firstName"]
    assert checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        checkout.shipping_address.street_address_1 == shipping_address["streetAddress1"]
    )
    assert (
        checkout.shipping_address.street_address_2 == shipping_address["streetAddress2"]
    )
    assert checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert checkout.shipping_address.country == shipping_address["country"]
    assert checkout.shipping_address.city == shipping_address["city"].upper()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.country == shipping_address["country"]
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_insufficient_stocks(
    mocked_update_shipping_method,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


def test_checkout_shipping_address_update_channel_without_shipping_zones(
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    checkout.channel.shipping_zones.clear()
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


def test_checkout_shipping_address_with_invalid_phone_number_returns_error(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+33600000"

    response = get_graphql_content(
        user_api_client.post_graphql(
            MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
            {
                "token": checkout.token,
                "shippingAddress": shipping_address,
            },
        )
    )["data"]["checkoutShippingAddressUpdate"]

    assert response["errors"] == [
        {
            "field": "phone",
            "message": "'+33600000' is not a valid phone number.",
            "code": CheckoutErrorCode.INVALID.name,
        }
    ]


@pytest.mark.parametrize(
    "number", ["+48321321888", "+44 (113) 892-1113", "00 44 (0) 20 7839 1377"]
)
def test_checkout_shipping_address_update_with_phone_country_prefix(
    number, user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = number
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


def test_checkout_shipping_address_update_without_phone_country_prefix(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+1-202-555-0132"
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


def test_checkout_billing_address_update(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    query = """
    mutation checkoutBillingAddressUpdate(
            $token: UUID, $billingAddress: AddressInput!) {
        checkoutBillingAddressUpdate(
                token: $token, billingAddress: $billingAddress) {
            checkout {
                token,
                id
            },
            errors {
                field,
                message
            }
        }
    }
    """
    billing_address = graphql_address_data

    variables = {"token": checkout_with_item.token, "billingAddress": billing_address}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutBillingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.billing_address is not None
    assert checkout.billing_address.first_name == billing_address["firstName"]
    assert checkout.billing_address.last_name == billing_address["lastName"]
    assert (
        checkout.billing_address.street_address_1 == billing_address["streetAddress1"]
    )
    assert (
        checkout.billing_address.street_address_2 == billing_address["streetAddress2"]
    )
    assert checkout.billing_address.postal_code == billing_address["postalCode"]
    assert checkout.billing_address.country == billing_address["country"]
    assert checkout.billing_address.city == billing_address["city"].upper()
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_address_update_exclude_shipping_method(
    mocked_webhook,
    user_api_client,
    checkout_with_items_and_shipping,
    graphql_address_data,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_items_and_shipping
    previous_last_change = checkout.last_change
    shipping_method = checkout.shipping_method
    assert shipping_method is not None
    webhook_reason = "hello-there"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]
    shipping_address = graphql_address_data
    variables = {"token": checkout.token, "shippingAddress": shipping_address}

    user_api_client.post_graphql(MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables)
    checkout.refresh_from_db()
    assert checkout.shipping_method is None
    assert checkout.last_change != previous_last_change


CHECKOUT_EMAIL_UPDATE_MUTATION = """
    mutation checkoutEmailUpdate($token: UUID, $email: String!) {
        checkoutEmailUpdate(token: $token, email: $email) {
            checkout {
                id,
                email
            },
            errors {
                field,
                message
            }
            errors {
                field,
                message
                code
            }
        }
    }
"""


def test_checkout_email_update(user_api_client, checkout_with_item):
    checkout = checkout_with_item
    assert not checkout.email
    previous_last_change = checkout.last_change

    email = "test@example.com"
    variables = {"token": checkout.token, "email": email}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutEmailUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.email == email
    assert checkout.last_change != previous_last_change


def test_checkout_email_update_validation(user_api_client, checkout_with_item):
    variables = {"token": checkout_with_item.token, "email": ""}

    response = user_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    previous_last_change = checkout_with_item.last_change

    errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "email"
    assert errors[0]["message"] == "This field cannot be blank."

    checkout_errors = content["data"]["checkoutEmailUpdate"]["errors"]
    assert checkout_errors[0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert checkout_with_item.last_change == previous_last_change


@pytest.fixture
def fake_manager(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def mock_get_manager(mocker, fake_manager):
    manager = mocker.patch(
        "saleor.payment.gateway.get_plugins_manager",
        autospec=True,
        return_value=fake_manager,
    )
    yield fake_manager
    manager.assert_called_once()


TRANSACTION_CONFIRM_GATEWAY_RESPONSE = GatewayResponse(
    is_success=False,
    action_required=False,
    kind=TransactionKind.CONFIRM,
    amount=Decimal(3.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)


QUERY_CHECKOUT_USER_ID = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           user {
               id
           }
        }
    }
    """


def test_anonymous_client_cant_fetch_checkout_user(api_client, checkout):
    query = QUERY_CHECKOUT_USER_ID
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_authorized_access_to_checkout_user_as_customer(
    user_api_client,
    checkout,
    customer_user,
):
    query = QUERY_CHECKOUT_USER_ID
    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["user"]["id"] == customer_user_id


def test_authorized_access_to_checkout_user_as_staff(
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_users,
    permission_manage_checkouts,
):
    query = QUERY_CHECKOUT_USER_ID
    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_users, permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["user"]["id"] == customer_user_id


def test_authorized_access_to_checkout_user_as_staff_no_permission(
    staff_api_client,
    checkout,
    customer_user,
    permission_manage_checkouts,
):
    query = QUERY_CHECKOUT_USER_ID

    checkout.user = customer_user
    checkout.save()

    variables = {"token": str(checkout.token)}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    assert_no_permission(response)


QUERY_CHECKOUT = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            token
        }
    }
"""


def test_query_anonymous_customer_checkout_as_anonymous_customer(api_client, checkout):
    variables = {"token": str(checkout.token), "channel": checkout.channel.slug}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


QUERY_CHECKOUT_CHANNEL_SLUG = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
            token
            channel {
                slug
            }
        }
    }
"""


def test_query_anonymous_customer_channel_checkout_as_anonymous_customer(
    api_client, checkout
):
    query = QUERY_CHECKOUT_CHANNEL_SLUG
    checkout_token = str(checkout.token)
    channel_slug = checkout.channel.slug
    variables = {"token": checkout_token}

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["token"] == checkout_token
    assert content["data"]["checkout"]["channel"]["slug"] == channel_slug


def test_query_anonymous_customer_channel_checkout_as_customer(
    user_api_client, checkout
):
    query = QUERY_CHECKOUT_CHANNEL_SLUG
    checkout_token = str(checkout.token)
    channel_slug = checkout.channel.slug
    variables = {
        "token": checkout_token,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkout"]["token"] == checkout_token
    assert content["data"]["checkout"]["channel"]["slug"] == channel_slug


def test_query_anonymous_customer_checkout_as_customer(user_api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_staff_user(
    staff_api_client, checkout, permission_manage_checkouts
):
    variables = {"token": str(checkout.token)}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_anonymous_customer_checkout_as_app(
    app_api_client, checkout, permission_manage_checkouts
):
    variables = {"token": str(checkout.token)}
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_anonymous_customer(
    api_client, checkout, customer_user
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_customer(user_api_client, checkout, customer_user):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_other_customer_checkout_as_customer(
    user_api_client, checkout, staff_user
):
    checkout.user = staff_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert not content["data"]["checkout"]


def test_query_customer_checkout_as_staff_user(
    app_api_client, checkout, customer_user, permission_manage_checkouts
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = app_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_query_customer_checkout_as_app(
    staff_api_client, checkout, customer_user, permission_manage_checkouts
):
    checkout.user = customer_user
    checkout.save(update_fields=["user"])
    variables = {"token": str(checkout.token)}
    response = staff_api_client.post_graphql(
        QUERY_CHECKOUT,
        variables,
        permissions=[permission_manage_checkouts],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_fetch_checkout_invalid_token(user_api_client, channel_USD):
    variables = {"token": str(uuid.uuid4())}
    response = user_api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data is None


def test_checkout_prices(user_api_client, checkout_with_item):
    query = """
    query getCheckout($token: UUID!) {
        checkout(token: $token) {
           token,
           totalPrice {
                currency
                gross {
                    amount
                }
            }
            subtotalPrice {
                currency
                gross {
                    amount
                }
            }
           lines {
                totalPrice {
                    currency
                    gross {
                        amount
                    }
                }
           }
        }
    }
    """
    variables = {"token": str(checkout_with_item.token)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    assert data["token"] == str(checkout_with_item.token)
    assert len(data["lines"]) == checkout_with_item.lines.count()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert data["totalPrice"]["gross"]["amount"] == (total.gross.amount)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert data["subtotalPrice"]["gross"]["amount"] == (subtotal.gross.amount)


MUTATION_UPDATE_SHIPPING_METHOD = """
    mutation checkoutShippingMethodUpdate(
            $token: UUID, $shippingMethodId: ID!){
        checkoutShippingMethodUpdate(
            token: $token, shippingMethodId: $shippingMethodId) {
            errors {
                field
                message
                code
            }
            checkout {
                token
            }
        }
    }
"""


@pytest.mark.parametrize("is_valid_shipping_method", (True, False))
@patch("saleor.graphql.checkout.mutations.clean_shipping_method")
def test_checkout_shipping_method_update(
    mock_clean_shipping,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    is_valid_shipping_method,
):
    checkout = checkout_with_item
    old_shipping_method = checkout.shipping_method
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_clean_shipping.return_value = is_valid_shipping_method
    previous_last_change = checkout.last_change

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"token": checkout_with_item.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    checkout_info.delivery_method_info = get_delivery_method_info(old_shipping_method)
    checkout_info.shipping_method_channel_listings = None
    mock_clean_shipping.assert_called_once_with(
        checkout_info=checkout_info, lines=lines, method=ANY
    )
    errors = data["errors"]
    if is_valid_shipping_method:
        assert not errors
        assert data["checkout"]["token"] == str(checkout_with_item.token)
        assert checkout.shipping_method == shipping_method
        assert checkout.last_change != previous_last_change
    else:
        assert len(errors) == 1
        assert errors[0]["field"] == "shippingMethod"
        assert (
            errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
        )
        assert checkout.shipping_method is None
        assert checkout.last_change == previous_last_change


@patch("saleor.shipping.postal_codes.is_shipping_method_applicable_for_postal_code")
def test_checkout_shipping_method_update_excluded_postal_code(
    mock_is_shipping_method_available,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    mock_is_shipping_method_available.return_value = False

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"token": checkout_with_item.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None
    assert (
        mock_is_shipping_method_available.call_count
        == shipping_models.ShippingMethod.objects.count()
    )


@patch(
    "saleor.plugins.webhook.plugin.WebhookPlugin.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_method_update_excluded_webhook(
    mocked_webhook,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "spanish-inquisition"

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]
    # when
    response = staff_api_client.post_graphql(
        query, {"token": checkout_with_item.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()
    # then
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_methods_webhook_called_once(
    mocked_webhook,
    staff_api_client,
    shipping_method,
    checkout_with_item,
    permission_manage_checkouts,
    settings,
):
    # given
    manager = get_plugins_manager()
    mocked_webhook.side_effect = [[], AssertionError("called twice.")]
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_SHIPPING_METHOD,
        {"token": checkout_with_item.token, "shippingMethodId": method_id},
    )
    get_graphql_content(response)
    fetch_checkout_info(checkout_with_item, [], [], manager)
    # then
    assert checkout_with_item.shipping_method is None


def test_checkout_shipping_method_update_shipping_zone_without_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    shipping_method.shipping_zone.channels.clear()
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"token": checkout_with_item.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert checkout.shipping_method is None


def test_checkout_shipping_method_update_shipping_zone_with_channel(
    staff_api_client,
    shipping_method,
    checkout_with_item,
    address,
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])
    query = MUTATION_UPDATE_SHIPPING_METHOD

    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)

    response = staff_api_client.post_graphql(
        query, {"token": checkout_with_item.token, "shippingMethodId": method_id}
    )
    data = get_graphql_content(response)["data"]["checkoutShippingMethodUpdate"]

    checkout.refresh_from_db()

    checkout.refresh_from_db()
    errors = data["errors"]
    assert not errors
    assert data["checkout"]["token"] == str(checkout_with_item.token)

    assert checkout.shipping_method == shipping_method


def test_query_checkouts(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    checkout = checkout_with_item
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    received_checkout = content["data"]["checkouts"]["edges"][0]["node"]
    assert str(checkout.token) == received_checkout["token"]


def test_query_with_channel(
    checkouts_list, staff_api_client, permission_manage_checkouts, channel_USD
):
    query = """
    query CheckoutsQuery($channel: String) {
        checkouts(first: 20, channel: $channel) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"]) == 3


def test_query_without_channel(
    checkouts_list, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkouts(first: 20) {
            edges {
                node {
                    token
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["checkouts"]["edges"]) == 5


def test_query_checkout_lines(
    checkout_with_item, staff_api_client, permission_manage_checkouts
):
    query = """
    {
        checkoutLines(first: 20) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    checkout = checkout_with_item
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_checkouts]
    )
    content = get_graphql_content(response)
    lines = content["data"]["checkoutLines"]["edges"]
    checkout_lines_ids = [line["node"]["id"] for line in lines]
    expected_lines_ids = [
        graphene.Node.to_global_id("CheckoutLine", item.pk) for item in checkout
    ]
    assert expected_lines_ids == checkout_lines_ids


def test_clean_checkout(checkout_with_item, payment_dummy, address, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    manager = get_plugins_manager()
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    # Shouldn't raise any errors

    clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
    clean_checkout_payment(
        manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
    )


def test_clean_checkout_no_shipping_method(checkout_with_item, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)

    msg = "Shipping method is not set"
    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_shipping_address(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
    msg = "Shipping address is not set"
    assert e.value.error_dict["shipping_address"][0].message == msg


def test_clean_checkout_invalid_shipping_method(
    checkout_with_item, address, shipping_zone_without_countries
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    shipping_method = shipping_zone_without_countries.shipping_methods.first()
    checkout.shipping_method = shipping_method
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    with pytest.raises(ValidationError) as e:
        clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)

    msg = "Shipping method is not valid for your shipping address"

    assert e.value.error_dict["shipping_method"][0].message == msg


def test_clean_checkout_no_billing_address(
    checkout_with_item, address, shipping_method
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.save()
    payment = checkout.get_last_active_payment()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
        )
    msg = "Billing address is not set"
    assert e.value.error_dict["billing_address"][0].message == msg


def test_clean_checkout_no_payment(checkout_with_item, shipping_method, address):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.save()
    payment = checkout.get_last_active_payment()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    with pytest.raises(ValidationError) as e:
        clean_checkout_payment(
            manager, checkout_info, lines, None, CheckoutErrorCode, last_payment=payment
        )

    msg = "Provided payment methods can not cover the checkout's total amount"
    assert e.value.error_list[0].message == msg


QUERY_CHECKOUT = """
    query getCheckout($token: UUID!){
        checkout(token: $token){
            id
            token
            lines{
                id
                variant{
                    id
                }
            }
            shippingPrice{
                currency
                gross {
                    amount
                }
                net {
                    amount
                }
            }
        }
    }
"""


def test_get_variant_data_from_checkout_line_variant_hidden_in_listings(
    checkout_with_item, api_client
):
    # given
    query = QUERY_CHECKOUT
    checkout = checkout_with_item
    variant = checkout.lines.get().variant
    variant.product.channel_listings.update(visible_in_listings=False)
    variables = {"token": checkout.token}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["lines"][0]["variant"]["id"]


@override_settings(PLUGINS=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"])
def test_get_checkout_with_vatlayer_set(
    checkout_with_item, api_client, vatlayer, site_settings, shipping_zone
):
    # given
    site_settings.include_taxes_in_prices = True
    site_settings.save()

    query = QUERY_CHECKOUT
    checkout = checkout_with_item
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    variant = checkout.lines.get().variant
    variant.product.channel_listings.update(visible_in_listings=False)
    variables = {"token": checkout.token}

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)
