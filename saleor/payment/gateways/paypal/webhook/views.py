import json
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import BadRequest, ValidationError
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from saleor.payment import ChargeStatus
from saleor.payment.models import Payment


@csrf_exempt
def paypal_webhook(request):
    event = json.loads(request.body)

    if event['event_type'] == 'PAYMENT.CAPTURE.REFUNDED':
        refund_amount = get_total_refund_amount(event)
        date = convert_paypal_date(event)
        psp_reference = get_capture_id(event)
        payment = Payment.objects.filter(psp_reference=psp_reference).first()

        if payment is not None:
            set_psp_data(payment, refund_amount, date)

    return HttpResponse(status=200)


def set_psp_data(payment, refund_amount, date):
    refund_value = Decimal(refund_amount['value'])
    refund_currency = refund_amount['currency_code']

    if refund_currency != 'EUR':
        raise ValidationError('Paypal Webhook Error: Invalid currency')

    if payment.total == refund_value:
        charge_status = ChargeStatus.FULLY_REFUNDED
    elif payment.total > refund_value > 0:
        charge_status = ChargeStatus.PARTIALLY_REFUNDED
    else:
        raise ValidationError('Paypal Webhook Error: Invalid refund amount')

    payment.psp_state = charge_status
    payment.psp_refund_amount = refund_value
    payment.psp_refund_date = date
    payment.save()


def get_total_refund_amount(event):
    return event['resource']['seller_payable_breakdown']['total_refunded_amount']


def convert_paypal_date(event):
    date_string = event['resource']['create_time']

    return datetime.fromisoformat(date_string)


def get_capture_id(event):
    # https://developer.paypal.com/api/rest/responses/#link-hateoaslinks
    links = event['resource']['links']

    for link in links:
        if link['rel'] == 'up':
            # https://stackoverflow.com/questions/7253803/how-to-get-everything-after-last-slash-in-a-url
            return link['href'].rsplit('/', 1)[-1]

    raise BadRequest('Paypal Webhook Error: Could not find referencing paypal capture')
