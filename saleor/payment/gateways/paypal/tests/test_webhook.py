from datetime import datetime
from decimal import Decimal

import pytest
from django.http import HttpResponse

from saleor.payment import ChargeStatus
from saleor.payment.gateways.paypal.webhook.views import paypal_webhook
from saleor.payment.models import Payment


def test_set_psp_to_refunded(
        paypal_refund_event,
        paypal_payment: Payment,
        paypal_payment_id: str,
):
    response = paypal_webhook(paypal_refund_event)
    actual = Payment.objects.filter(id=paypal_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state == ChargeStatus.FULLY_REFUNDED
    assert actual.psp_refund_amount == pytest.approx(Decimal(4.900))
    assert actual.psp_refund_date == datetime.fromisoformat('2022-10-19T09:16:59-07:00')


def test_set_psp_to_partially_refunded(
        paypal_partial_refund_event,
        paypal_payment: Payment,
        paypal_payment_id: str,
):
    response = paypal_webhook(paypal_partial_refund_event)
    actual = Payment.objects.filter(id=paypal_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state == ChargeStatus.PARTIALLY_REFUNDED
    assert actual.psp_refund_amount == pytest.approx(Decimal(2.900))
    assert actual.psp_refund_date == datetime.fromisoformat('2022-10-20T02:01:39-07:00')


def test_ignore_payment_capture(
        paypal_payment_capture,
        paypal_payment: Payment,
        paypal_payment_id: str,
):
    response = paypal_webhook(paypal_payment_capture)
    actual = Payment.objects.filter(id=paypal_payment.id).first()

    assert response.status_code == 200
    assert actual.psp_state is None
