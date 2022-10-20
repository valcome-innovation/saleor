import json
from unittest import mock

import pytest


@pytest.fixture()
def paypal_payment(payment_dummy, paypal_payment_id):
    payment_dummy.gateway = 'mirumee.payments.paypal'
    payment_dummy.psp_reference = paypal_payment_id
    payment_dummy.total = 4.9
    payment_dummy.save()

    return payment_dummy


@pytest.fixture()
def paypal_payment_id():
    return "3A156903W71171418"


@pytest.fixture()
def paypal_refund_event(paypal_payment_id):
    event = mock.Mock()
    event.body = json.dumps({
        "id": "WH-2UF70599HW932373X-2F986831JR810362G",
        "event_version": "1.0",
        "create_time": "2022-10-19T16:17:04.008Z",
        "resource_type": "refund",
        "resource_version": "2.0",
        "event_type": "PAYMENT.CAPTURE.REFUNDED",
        "summary": "A EUR 4.9 EUR capture payment was refunded",
        "resource": {
            "seller_payable_breakdown": {
                "total_refunded_amount": {
                    "value": "4.90",
                    "currency_code": "EUR"
                },
                "paypal_fee": {
                    "value": "0.17",
                    "currency_code": "EUR"
                },
                "gross_amount": {
                    "value": "4.90",
                    "currency_code": "EUR"
                },
                "net_amount": {
                    "value": "4.73",
                    "currency_code": "EUR"
                }
            },
            "amount": {
                "value": "4.90",
                "currency_code": "EUR"
            },
            "update_time": "2022-10-19T09:16:59-07:00",
            "create_time": "2022-10-19T09:16:59-07:00",
            "links": [
                {
                    "method": "GET",
                    "rel": "self",
                    "href": "https://api.sandbox.paypal.com/v2/payments/refunds/1MK466489E6177644"
                },
                {
                    "method": "GET",
                    "rel": "up",
                    "href": "https://api.sandbox.paypal.com/v2/payments/captures/" + paypal_payment_id
                }
            ],
            "id": "1MK466489E6177644",
            "status": "COMPLETED"
        },
        "links": [
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-2UF70599HW932373X-2F986831JR810362G",
                "rel": "self",
                "method": "GET"
            },
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-2UF70599HW932373X-2F986831JR810362G/resend",
                "rel": "resend",
                "method": "POST"
            }
        ]
    })

    return event


@pytest.fixture()
def paypal_partial_refund_event(paypal_payment_id):
    event = mock.Mock()
    event.body = json.dumps({
        "id": "WH-1CV20338EX520823B-4M746371UM696663G",
        "event_version": "1.0",
        "create_time": "2022-10-20T09:01:44.099Z",
        "resource_type": "refund",
        "resource_version": "2.0",
        "event_type": "PAYMENT.CAPTURE.REFUNDED",
        "summary": "A EUR 2.9 EUR capture payment was refunded",
        "resource": {
            "seller_payable_breakdown": {
                "total_refunded_amount": {
                    "value": "2.90",
                    "currency_code": "EUR"
                },
                "paypal_fee": {
                    "value": "0.10",
                    "currency_code": "EUR"
                },
                "gross_amount": {
                    "value": "2.90",
                    "currency_code": "EUR"
                },
                "net_amount": {
                    "value": "2.80",
                    "currency_code": "EUR"
                }
            },
            "amount": {
                "value": "2.90",
                "currency_code": "EUR"
            },
            "update_time": "2022-10-20T02:01:39-07:00",
            "create_time": "2022-10-20T02:01:39-07:00",
            "links": [
                {
                    "method": "GET",
                    "rel": "self",
                    "href": "https://api.sandbox.paypal.com/v2/payments/refunds/69B23728H3998760A"
                },
                {
                    "method": "GET",
                    "rel": "up",
                    "href": "https://api.sandbox.paypal.com/v2/payments/captures/" + paypal_payment_id
                }
            ],
            "id": "69B23728H3998760A",
            "status": "COMPLETED"
        },
        "links": [
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-1CV20338EX520823B-4M746371UM696663G",
                "rel": "self",
                "method": "GET"
            },
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-1CV20338EX520823B-4M746371UM696663G/resend",
                "rel": "resend",
                "method": "POST"
            }
        ]
    })

    return event


@pytest.fixture()
def paypal_payment_capture(paypal_payment_id):
    event = mock.Mock()
    event.body = json.dumps({
        "id": "WH-3EN26566WY197832S-3LY11387V2223933V",
        "event_version": "1.0",
        "create_time": "2022-10-19T16:15:40.012Z",
        "resource_type": "capture",
        "resource_version": "2.0",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "summary": "Payment completed for EUR 4.9 EUR",
        "resource": {
            "amount": {
                "value": "4.90",
                "currency_code": "EUR"
            },
            "seller_protection": {
                "dispute_categories": [
                    "ITEM_NOT_RECEIVED",
                    "UNAUTHORIZED_TRANSACTION"
                ],
                "status": "ELIGIBLE"
            },
            "supplementary_data": {
                "related_ids": {
                    "order_id": "64192477F66551946"
                }
            },
            "update_time": "2022-10-19T16:15:35Z",
            "create_time": "2022-10-19T16:15:35Z",
            "final_capture": "true",
            "seller_receivable_breakdown": {
                "paypal_fee": {
                    "value": "0.52",
                    "currency_code": "EUR"
                },
                "gross_amount": {
                    "value": "4.90",
                    "currency_code": "EUR"
                },
                "net_amount": {
                    "value": "4.38",
                    "currency_code": "EUR"
                }
            },
            "links": [
                {
                    "method": "GET",
                    "rel": "self",
                    "href": "https://api.sandbox.paypal.com/v2/payments/captures/3A156903W71171418"
                },
                {
                    "method": "POST",
                    "rel": "refund",
                    "href": "https://api.sandbox.paypal.com/v2/payments/captures/3A156903W71171418/refund"
                },
                {
                    "method": "GET",
                    "rel": "up",
                    "href": "https://api.sandbox.paypal.com/v2/checkout/orders/64192477F66551946"
                }
            ],
            "id": paypal_payment_id,
            "status": "COMPLETED"
        },
        "links": [
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-3EN26566WY197832S-3LY11387V2223933V",
                "rel": "self",
                "method": "GET"
            },
            {
                "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-3EN26566WY197832S-3LY11387V2223933V/resend",
                "rel": "resend",
                "method": "POST"
            }
        ]
    })

    return event
