from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError

from saleor.payment import ChargeStatus
from saleor.payment.models import Payment


def update_refund_psp_data(charge):
    psp_reference = charge.payment_intent
    payment = Payment.objects.filter(psp_reference=psp_reference).first()

    if payment is not None and payment.psp_state != ChargeStatus.REFUSED:
        refund_value = Decimal(charge.amount_refunded) / Decimal(100)  # cents to euros
        refund_date = get_latest_refund_date(charge.refunds.data)

        if charge.currency.lower() != 'eur':
            raise ValidationError('Stripe Webhook Error: Invalid currency')

        if payment.total == refund_value:
            charge_status = ChargeStatus.FULLY_REFUNDED
        elif payment.total > refund_value > 0:
            charge_status = ChargeStatus.PARTIALLY_REFUNDED
        else:
            raise ValidationError('Stripe Webhook Error: Invalid refund amount')

        payment.psp_state = charge_status
        payment.psp_refund_amount = refund_value
        payment.psp_refund_date = refund_date
        payment.save()


def get_latest_refund_date(refunds):
    latest_unix = None

    for refund in refunds:
        if latest_unix is None or refund.created > latest_unix:
            latest_unix = refund.created

    if latest_unix is not None:
        return datetime.fromtimestamp(latest_unix)


def update_sofort_failure_psp_data(payment_intent):
    psp_reference = payment_intent.id
    payment = Payment.objects.filter(psp_reference=psp_reference).first()

    if payment is not None:
        payment.psp_state = ChargeStatus.REFUSED
        payment.save()
