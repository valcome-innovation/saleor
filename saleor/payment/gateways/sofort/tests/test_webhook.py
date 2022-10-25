from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from saleor.checkout.models import Checkout
from saleor.graphql.checkout.mutations import CheckoutComplete
from saleor.payment import ChargeStatus
from saleor.payment.gateways.sofort.webhook.views import stripe_webhook
from saleor.payment.models import Payment


@patch.object(CheckoutComplete, 'perform_mutation')
def test_create_order_for_processing_sofort(
        checkout_complete_mock,
        stripe_sofort_processing_event,
        stripe_checkout: Checkout,
):
    stripe_checkout.save()

    stripe_webhook(stripe_sofort_processing_event)

    assert checkout_complete_mock.called


@patch.object(CheckoutComplete, 'perform_mutation')
def test_ignore_processing_checkouts(
        checkout_complete_mock,
        stripe_sofort_processing_event,
        stripe_checkout: Checkout,
):
    stripe_checkout.webhook_processing = True
    stripe_checkout.save()

    stripe_webhook(stripe_sofort_processing_event)

    assert not checkout_complete_mock.called


# https://miguendes.me/how-to-use-fixtures-as-arguments-in-pytestmarkparametrize
@pytest.mark.parametrize('refund_event_fixture', [
    'stripe_sofort_refund_event',
    'stripe_cc_refund_event'
])
def test_psp_data_to_fully_refund(
        refund_event_fixture,
        stripe_webhook_payment,
        request
):
    refund_event = request.getfixturevalue(refund_event_fixture)

    response = stripe_webhook(refund_event)
    actual = Payment.objects.filter(id=stripe_webhook_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state == ChargeStatus.FULLY_REFUNDED
    assert actual.psp_refund_amount == pytest.approx(Decimal(4.900))
    assert actual.psp_refund_date == datetime.fromisoformat('2022-10-19T15:58:03+00:00')


def test_psp_data_to_partially_refund(
        stripe_cc_partial_refund_event,
        stripe_webhook_payment
):
    response = stripe_webhook(stripe_cc_partial_refund_event)
    actual = Payment.objects.filter(id=stripe_webhook_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state == ChargeStatus.PARTIALLY_REFUNDED
    assert actual.psp_refund_amount == pytest.approx(Decimal(4.800))
    assert actual.psp_refund_date == datetime.fromisoformat('2022-10-21T12:29:47+00:00')


# https://miguendes.me/how-to-use-fixtures-as-arguments-in-pytestmarkparametrize
@pytest.mark.parametrize('fail_event_fixture', [
    'stripe_sofort_fail_instant_event',
    'stripe_sofort_fail_later_event'
])
def test_psp_data_to_refused(
        fail_event_fixture,
        stripe_webhook_payment,
        request
):
    fail_event = request.getfixturevalue(fail_event_fixture)

    response = stripe_webhook(fail_event)
    actual = Payment.objects.filter(id=stripe_webhook_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state == ChargeStatus.REFUSED
    assert actual.psp_refund_amount is None
    assert actual.psp_refund_date is None


def test_ignore_cc_failures(
        stripe_cc_fail_instant_event,
        stripe_webhook_payment
):
    response = stripe_webhook(stripe_cc_fail_instant_event)
    actual = Payment.objects.filter(id=stripe_webhook_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state is None
    assert actual.psp_refund_amount is None
    assert actual.psp_refund_date is None


def test_no_refund_for_failed_payment(
        stripe_sofort_fail_later_event,
        stripe_sofort_refund_event,
        stripe_webhook_payment
):
    stripe_webhook(stripe_sofort_fail_later_event)
    stripe_webhook(stripe_sofort_refund_event)

    actual = Payment.objects.filter(id=stripe_webhook_payment.id).first()

    assert actual.psp_state == ChargeStatus.REFUSED
    assert actual.psp_refund_amount is None
    assert actual.psp_refund_date is None
