import json
from unittest import mock

import pytest

from saleor.checkout.models import Checkout
from saleor.payment import TransactionKind


@pytest.fixture
def stripe_checkout_token():
    return "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"


@pytest.fixture
def stripe_payment_intent_id():
    return "pi_3LueggH8gEfhfk0t1APAIgKx"


@pytest.fixture
def stripe_checkout(
        checkout: Checkout,
        stripe_checkout_token
):
    checkout.token = stripe_checkout_token
    checkout.webhook_processing = False

    checkout.save()

    return checkout


@pytest.fixture()
def stripe_webhook_payment(payment_dummy,
                           stripe_payment_intent_id,
                           stripe_checkout: Checkout):
    payment_dummy.gateway = 'saleor.payments.stripe'
    payment_dummy.psp_reference = stripe_payment_intent_id
    payment_dummy.total = 4.9
    payment_dummy.checkout = stripe_checkout
    payment_dummy.order = None

    payment_dummy.transactions.create(
        amount=4.9,
        currency='EUR',
        kind=TransactionKind.AUTH,
        token=stripe_payment_intent_id,
        gateway_response={},
        is_success=True,
    )

    return payment_dummy


@pytest.fixture
def stripe_sofort_processing_event():
    event = mock.Mock()
    event.body = json.dumps({
        "id": "evt_3LueggH8gEfhfk0t1RwyXL4t",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666195227,
        "data": {
            "object": {
                "id": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "object": "payment_intent",
                "amount": 490,
                "amount_capturable": 0,
                "amount_details": {
                    "tip": {}
                },
                "amount_received": 0,
                "application": None,
                "application_fee_amount": None,
                "automatic_payment_methods": None,
                "canceled_at": None,
                "cancellation_reason": None,
                "capture_method": "automatic",
                "charges": {
                    "object": "list",
                    "data": [
                        {
                            "id": "py_3LueggH8gEfhfk0t17gmuyIG",
                            "object": "charge",
                            "amount": 490,
                            "amount_captured": 490,
                            "amount_refunded": 0,
                            "application": None,
                            "application_fee": None,
                            "application_fee_amount": None,
                            "balance_transaction": None,
                            "billing_details": {
                                "address": {
                                    "city": None,
                                    "country": "BE",
                                    "line1": None,
                                    "line2": None,
                                    "postal_code": None,
                                    "state": None
                                },
                                "email": "simon.kepplinger@gmail.com",
                                "name": "Test Test",
                                "phone": None
                            },
                            "calculated_statement_descriptor": None,
                            "captured": True,
                            "created": 1666195227,
                            "currency": "eur",
                            "customer": "cus_Mdvs7sdi0PkKz7",
                            "description": None,
                            "destination": None,
                            "dispute": None,
                            "disputed": False,
                            "failure_balance_transaction": None,
                            "failure_code": None,
                            "failure_message": None,
                            "fraud_details": {},
                            "invoice": None,
                            "livemode": False,
                            "metadata": {
                                "checkout_params": "{\"product\":\"UHJvZHVjdDo5\",\"stp\":\"g\",\"g\":\"d4z8yn94viml9fryaka\"}",
                                "app_id": "VTV",
                                "redirect_id": "d4z8yn94viml9fryaka",
                                "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"
                            },
                            "on_behalf_of": None,
                            "order": None,
                            "outcome": {
                                "network_status": "approved_by_network",
                                "reason": None,
                                "risk_level": "not_assessed",
                                "seller_message": "Payment complete.",
                                "type": "authorized"
                            },
                            "paid": False,
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "payment_method": "pm_1LueghH8gEfhfk0tsqgvAx52",
                            "payment_method_details": {
                                "sofort": {
                                    "bank_code": "DEUT",
                                    "bank_name": "Deutsche Bank",
                                    "bic": "DEUTDE2H",
                                    "country": "BE",
                                    "generated_sepa_debit": None,
                                    "generated_sepa_debit_mandate": None,
                                    "iban_last4": "3000",
                                    "preferred_language": None,
                                    "verified_name": "Jenny Rosen"
                                },
                                "type": "sofort"
                            },
                            "receipt_email": None,
                            "receipt_number": None,
                            "receipt_url": None,
                            "refunded": False,
                            "refunds": {
                                "object": "list",
                                "data": [],
                                "has_more": False,
                                "total_count": 0,
                                "url": "/v1/charges/py_3LueggH8gEfhfk0t17gmuyIG/refunds"
                            },
                            "review": None,
                            "shipping": None,
                            "source": None,
                            "source_transfer": None,
                            "statement_descriptor": None,
                            "statement_descriptor_suffix": None,
                            "status": "pending",
                            "transfer_data": None,
                            "transfer_group": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 1,
                    "url": "/v1/charges?payment_intent=pi_3LueggH8gEfhfk0t1APAIgKx"
                },
                "client_secret": "secret",
                "confirmation_method": "automatic",
                "created": 1666195210,
                "currency": "eur",
                "customer": "cus_Mdvs7sdi0PkKz7",
                "description": None,
                "invoice": None,
                "last_payment_error": None,
                "livemode": False,
                "metadata": {
                    "checkout_params": "{\"product\":\"UHJvZHVjdDo5\",\"stp\":\"g\",\"g\":\"d4z8yn94viml9fryaka\"}",
                    "app_id": "VTV",
                    "redirect_id": "d4z8yn94viml9fryaka",
                    "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"
                },
                "next_action": None,
                "on_behalf_of": None,
                "payment_method": "pm_1LueghH8gEfhfk0tsqgvAx52",
                "payment_method_options": {
                    "sofort": {
                        "preferred_language": None
                    }
                },
                "payment_method_types": [
                    "sofort"
                ],
                "processing": None,
                "receipt_email": None,
                "review": None,
                "setup_future_usage": None,
                "shipping": None,
                "source": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "processing",
                "transfer_data": None,
                "transfer_group": None
            }
        },
        "livemode": False,
        "pending_webhooks": 4,
        "request": {
            "id": None,
            "idempotency_key": "42b880eb-1538-4aa8-8fd0-3d6b22503bd9"
        },
        "type": "payment_intent.processing"
    })

    return event


@pytest.fixture
def stripe_cc_refund_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3LmaWRH8gEfhfk0t0NvNjgHd",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666194979,
        "data": {
            "object": {
                "id": "ch_3LmaWRH8gEfhfk0t0OdDRc9k",
                "object": "charge",
                "amount": 490,
                "amount_captured": 490,
                "amount_refunded": 490,
                "application": None,
                "application_fee": None,
                "application_fee_amount": None,
                "balance_transaction": "txn_3LmaWRH8gEfhfk0t0Dgdab90",
                "billing_details": {
                    "address": {
                        "city": None,
                        "country": "AT",
                        "line1": None,
                        "line2": None,
                        "postal_code": None,
                        "state": None
                    },
                    "email": "simon.kepplinger@gmail.com",
                    "name": "Simon Kepplinger",
                    "phone": None
                },
                "calculated_statement_descriptor": "ICEHOCKEY LIVESTREAM",
                "captured": True,
                "created": 1664272577,
                "currency": "eur",
                "customer": "cus_MVbilNsMdn0x3w",
                "description": None,
                "destination": None,
                "dispute": None,
                "disputed": False,
                "failure_balance_transaction": None,
                "failure_code": None,
                "failure_message": None,
                "fraud_details": {},
                "invoice": None,
                "livemode": False,
                "metadata": {
                    "channel": "streaming-channel",
                    "payment_id": "UGF5bWVudDoy"
                },
                "on_behalf_of": None,
                "order": None,
                "outcome": {
                    "network_status": "approved_by_network",
                    "reason": None,
                    "risk_level": "normal",
                    "risk_score": 9,
                    "seller_message": "Payment complete.",
                    "type": "authorized"
                },
                "paid": True,
                "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "payment_method": "pm_1LmaWQH8gEfhfk0tr1cZOcHR",
                "payment_method_details": {
                    "card": {
                        "brand": "visa",
                        "checks": {
                            "address_line1_check": None,
                            "address_postal_code_check": None,
                            "cvc_check": "pass"
                        },
                        "country": "US",
                        "exp_month": 2,
                        "exp_year": 2042,
                        "fingerprint": "16GUWWVRomf1xICD",
                        "funding": "credit",
                        "installments": None,
                        "last4": "4242",
                        "mandate": None,
                        "network": "visa",
                        "three_d_secure": None,
                        "wallet": None
                    },
                    "type": "card"
                },
                "receipt_email": None,
                "receipt_number": None,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KKO8wJoGMgaPVNfP10M6LBaPEZeNIM4BTIS1TgipRyHS4j8n1zdUoZTL8HG2MfaadK6ueJ8LWwPdR_dM",
                "refunded": True,
                "refunds": {
                    "object": "list",
                    "data": [
                        {
                            "id": "re_3LmaWRH8gEfhfk0t0ABPefbe",
                            "object": "refund",
                            "amount": 490,
                            "balance_transaction": "txn_3LmaWRH8gEfhfk0t02Fkv7Sa",
                            "charge": "ch_3LmaWRH8gEfhfk0t0OdDRc9k",
                            "created": 1666195083,
                            "currency": "eur",
                            "metadata": {},
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "reason": "requested_by_customer",
                            "receipt_number": None,
                            "source_transfer_reversal": None,
                            "status": "succeeded",
                            "transfer_reversal": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 1,
                    "url": "/v1/charges/ch_3LmaWRH8gEfhfk0t0OdDRc9k/refunds"
                },
                "review": None,
                "shipping": None,
                "source": None,
                "source_transfer": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "succeeded",
                "transfer_data": None,
                "transfer_group": None
            },
            "previous_attributes": {
                "amount_refunded": 0,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KKK8wJoGMgYFfN5N6sw6LBZV4h8DTBA2B9sumxY7WV0_VvoTzgsxzQznj9dZHYbQtJEGF_W--4nKlovA",
                "refunded": False,
                "refunds": {
                    "data": [],
                    "total_count": 0
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 2,
        "request": {
            "id": "req_jweLesx2z5PRBz",
            "idempotency_key": "a4d6971f-2729-4079-8698-5784fe0c8f86"
        },
        "type": "charge.refunded"
    })

    return request


@pytest.fixture
def stripe_sofort_refund_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3Lmw3lH8gEfhfk0t17n3hRT4",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666195084,
        "data": {
            "object": {
                "id": "py_3Lmw3lH8gEfhfk0t1dx74jHA",
                "object": "charge",
                "amount": 490,
                "amount_captured": 490,
                "amount_refunded": 490,
                "application": None,
                "application_fee": None,
                "application_fee_amount": None,
                "balance_transaction": "txn_3Lmw3lH8gEfhfk0t1Au8Qrcd",
                "billing_details": {
                    "address": {
                        "city": None,
                        "country": "AT",
                        "line1": None,
                        "line2": None,
                        "postal_code": None,
                        "state": None
                    },
                    "email": "simon.kepplinger@gmail.com",
                    "name": "Simon Kepplinger",
                    "phone": None
                },
                "calculated_statement_descriptor": None,
                "captured": True,
                "created": 1664355372,
                "currency": "eur",
                "customer": "cus_MVxzwTkavpdVzb",
                "description": None,
                "destination": None,
                "dispute": None,
                "disputed": False,
                "failure_balance_transaction": None,
                "failure_code": None,
                "failure_message": None,
                "fraud_details": {},
                "invoice": None,
                "livemode": False,
                "metadata": {
                    "checkout_params": "{\"product\":\"UHJvZHVjdDo2MQ==\",\"stp\":\"g\",\"e\":\"d\",\"st\":1664323200,\"l\":[\"pi2lFENKxqMlTJEF\"]}",
                    "app_id": "VTV",
                    "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"
                },
                "on_behalf_of": None,
                "order": None,
                "outcome": {
                    "network_status": "approved_by_network",
                    "reason": None,
                    "risk_level": "not_assessed",
                    "seller_message": "Payment complete.",
                    "type": "authorized"
                },
                "paid": True,
                "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "payment_method": "pm_1Lmw3mH8gEfhfk0tRAcHyDhk",
                "payment_method_details": {
                    "sofort": {
                        "bank_code": "DEUT",
                        "bank_name": "Deutsche Bank",
                        "bic": "DEUTDE2H",
                        "country": "AT",
                        "generated_sepa_debit": None,
                        "generated_sepa_debit_mandate": None,
                        "iban_last4": "3000",
                        "preferred_language": None,
                        "verified_name": "Jenny Rosen"
                    },
                    "type": "sofort"
                },
                "receipt_email": None,
                "receipt_number": None,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KIy9wJoGMgbvjaeIuak6LBZ34UpBNlvQBBRk9OKRgpjfDO0Iww9Vthy7rmXIVYjTJrp32VSas8CWsZlT",
                "refunded": True,
                "refunds": {
                    "object": "list",
                    "data": [
                        {
                            "id": "pyr_1LueedH8gEfhfk0tu1TyZSmU",
                            "object": "refund",
                            "amount": 490,
                            "balance_transaction": "txn_1LueedH8gEfhfk0tmYJATkSN",
                            "charge": "py_3Lmw3lH8gEfhfk0t1dx74jHA",
                            "created": 1666195083,
                            "currency": "eur",
                            "metadata": {},
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "reason": "requested_by_customer",
                            "receipt_number": None,
                            "source_transfer_reversal": None,
                            "status": "pending",
                            "transfer_reversal": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 1,
                    "url": "/v1/charges/py_3Lmw3lH8gEfhfk0t1dx74jHA/refunds"
                },
                "review": None,
                "shipping": None,
                "source": None,
                "source_transfer": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "succeeded",
                "transfer_data": None,
                "transfer_group": None
            },
            "previous_attributes": {
                "amount_refunded": 0,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KIu9wJoGMgZv65nbFjk6LBbfocoPug4C4cSuLp_UKlF-o1wXVGe84ptIfotOMW-_zSwPfM2nXUDfnpMg",
                "refunded": False,
                "refunds": {
                    "data": [],
                    "total_count": 0
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 2,
        "request": {
            "id": "req_eglCmicpuPQJPW",
            "idempotency_key": "5a8341de-afa0-470c-92c2-7fbfbb70c2e2"
        },
        "type": "charge.refunded"
    })

    return request


@pytest.fixture
def stripe_cc_partial_refund_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3LvKJIH8gEfhfk0t1bWgXgdG",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666355387,
        "data": {
            "object": {
                "id": "ch_3LvKJIH8gEfhfk0t1QFEVISF",
                "object": "charge",
                "amount": 490,
                "amount_captured": 490,
                "amount_refunded": 480,
                "application": None,
                "application_fee": None,
                "application_fee_amount": None,
                "balance_transaction": "txn_3LvKJIH8gEfhfk0t1Xx9smzT",
                "billing_details": {
                    "address": {
                        "city": None,
                        "country": "BE",
                        "line1": None,
                        "line2": None,
                        "postal_code": None,
                        "state": None
                    },
                    "email": "simon.kepplinger@gmail.com",
                    "name": "Simo Kepp",
                    "phone": None
                },
                "calculated_statement_descriptor": "ICEHOCKEY LIVESTREAM",
                "captured": True,
                "created": 1666355209,
                "currency": "eur",
                "customer": "cus_MedaPsA8mJt0dk",
                "description": None,
                "destination": None,
                "dispute": None,
                "disputed": False,
                "failure_balance_transaction": None,
                "failure_code": None,
                "failure_message": None,
                "fraud_details": {},
                "invoice": None,
                "livemode": False,
                "metadata": {
                    "channel": "streaming-channel",
                    "payment_id": "UGF5bWVudDox"
                },
                "on_behalf_of": None,
                "order": None,
                "outcome": {
                    "network_status": "approved_by_network",
                    "reason": None,
                    "risk_level": "normal",
                    "risk_score": 10,
                    "seller_message": "Payment complete.",
                    "type": "authorized"
                },
                "paid": True,
                "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "payment_method": "pm_1LvKJGH8gEfhfk0tx6UZrWb7",
                "payment_method_details": {
                    "card": {
                        "brand": "visa",
                        "checks": {
                            "address_line1_check": None,
                            "address_postal_code_check": None,
                            "cvc_check": "pass"
                        },
                        "country": "US",
                        "exp_month": 4,
                        "exp_year": 2024,
                        "fingerprint": "16GUWWVRomf1xICD",
                        "funding": "credit",
                        "installments": None,
                        "last4": "4242",
                        "mandate": None,
                        "network": "visa",
                        "three_d_secure": None,
                        "wallet": None
                    },
                    "type": "card"
                },
                "receipt_email": None,
                "receipt_number": None,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KLuhypoGMgYtmNbm0Dk6LBZeVrnDG7YinBEqPkqiFjYoXcLUvs2LNZuZXMEfvpUQFcHByVbRL2MvIoKQ",
                "refunded": True,
                "refunds": {
                    "object": "list",
                    "data": [
                        {
                            "id": "re_3LvKJIH8gEfhfk0t1wwa23Fo",
                            "object": "refund",
                            "amount": 280,
                            "balance_transaction": "txn_3LvKJIH8gEfhfk0t1UiaUke8",
                            "charge": "ch_3LvKJIH8gEfhfk0t1QFEVISF",
                            "created": 1666355387,
                            "currency": "eur",
                            "metadata": {},
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "reason": "requested_by_customer",
                            "receipt_number": None,
                            "source_transfer_reversal": None,
                            "status": "succeeded",
                            "transfer_reversal": None
                        },
                        {
                            "id": "re_3LvKJIH8gEfhfk0t1GG4W1dt",
                            "object": "refund",
                            "amount": 200,
                            "balance_transaction": "txn_3LvKJIH8gEfhfk0t1pgF0oMC",
                            "charge": "ch_3LvKJIH8gEfhfk0t1QFEVISF",
                            "created": 1666355371,
                            "currency": "eur",
                            "metadata": {},
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "reason": "requested_by_customer",
                            "receipt_number": None,
                            "source_transfer_reversal": None,
                            "status": "succeeded",
                            "transfer_reversal": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 2,
                    "url": "/v1/charges/ch_3LvKJIH8gEfhfk0t1QFEVISF/refunds"
                },
                "review": None,
                "shipping": None,
                "source": None,
                "source_transfer": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "succeeded",
                "transfer_data": None,
                "transfer_group": None
            },
            "previous_attributes": {
                "amount_refunded": 200,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xRzZCdzBIOGdFZmhmazB0KLqhypoGMgaeNoIAthE6LBaxQPhec8ouPTtR39XtK8__07lD51IjYvpnJo4F6vsN5BfeUTlbrmupecmE",
                "refunded": False,
                "refunds": {
                    "data": [
                        {
                            "id": "re_3LvKJIH8gEfhfk0t1GG4W1dt",
                            "object": "refund",
                            "amount": 200,
                            "balance_transaction": "txn_3LvKJIH8gEfhfk0t1pgF0oMC",
                            "charge": "ch_3LvKJIH8gEfhfk0t1QFEVISF",
                            "created": 1666355371,
                            "currency": "eur",
                            "metadata": {},
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "reason": "requested_by_customer",
                            "receipt_number": None,
                            "source_transfer_reversal": None,
                            "status": "succeeded",
                            "transfer_reversal": None
                        }
                    ],
                    "total_count": 1
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 2,
        "request": {
            "id": "req_45FHicElzpT6ly",
            "idempotency_key": "1be83b79-1f5d-4c51-8081-aaca2ae844f3"
        },
        "type": "charge.refunded"
    })

    return request


@pytest.fixture
def stripe_sofort_fail_later_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3LueggH8gEfhfk0t15dLNsfG",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666195410,
        "data": {
            "object": {
                "id": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "object": "payment_intent",
                "amount": 490,
                "amount_capturable": 0,
                "amount_details": {
                    "tip": {}
                },
                "amount_received": 0,
                "application": None,
                "application_fee_amount": None,
                "automatic_payment_methods": None,
                "canceled_at": None,
                "cancellation_reason": None,
                "capture_method": "automatic",
                "charges": {
                    "object": "list",
                    "data": [
                        {
                            "id": "py_3LueggH8gEfhfk0t17gmuyIG",
                            "object": "charge",
                            "amount": 490,
                            "amount_captured": 490,
                            "amount_refunded": 0,
                            "application": None,
                            "application_fee": None,
                            "application_fee_amount": None,
                            "balance_transaction": None,
                            "billing_details": {
                                "address": {
                                    "city": None,
                                    "country": "BE",
                                    "line1": None,
                                    "line2": None,
                                    "postal_code": None,
                                    "state": None
                                },
                                "email": "simon.kepplinger@gmail.com",
                                "name": "Test Test",
                                "phone": None
                            },
                            "calculated_statement_descriptor": None,
                            "captured": True,
                            "created": 1666195227,
                            "currency": "eur",
                            "customer": "cus_Mdvs7sdi0PkKz7",
                            "description": None,
                            "destination": None,
                            "dispute": None,
                            "disputed": False,
                            "failure_balance_transaction": None,
                            "failure_code": "payment_intent_authentication_failure",
                            "failure_message": "The provided PaymentMethod has failed authentication. You can provide payment_method_data or a new PaymentMethod to attempt to fulfill this PaymentIntent again.",
                            "fraud_details": {},
                            "invoice": None,
                            "livemode": False,
                            "metadata": {
                                "checkout_params": "{\"product\":\"UHJvZHVjdDo5\",\"stp\":\"g\",\"g\":\"d4z8yn94viml9fryaka\"}",
                                "app_id": "VTV",
                                "redirect_id": "d4z8yn94viml9fryaka",
                                "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"
                            },
                            "on_behalf_of": None,
                            "order": None,
                            "outcome": {
                                "network_status": "declined_by_network",
                                "reason": "generic_decline",
                                "risk_level": "not_assessed",
                                "seller_message": "The bank did not return any further details with this decline.",
                                "type": "issuer_declined"
                            },
                            "paid": False,
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "payment_method": "pm_1LueghH8gEfhfk0tsqgvAx52",
                            "payment_method_details": {
                                "sofort": {
                                    "bank_code": "DEUT",
                                    "bank_name": "Deutsche Bank",
                                    "bic": "DEUTDE2H",
                                    "country": "BE",
                                    "generated_sepa_debit": None,
                                    "generated_sepa_debit_mandate": None,
                                    "iban_last4": "3000",
                                    "preferred_language": None,
                                    "verified_name": "Jenny Rosen"
                                },
                                "type": "sofort"
                            },
                            "receipt_email": None,
                            "receipt_number": None,
                            "receipt_url": None,
                            "refunded": False,
                            "refunds": {
                                "object": "list",
                                "data": [],
                                "has_more": False,
                                "total_count": 0,
                                "url": "/v1/charges/py_3LueggH8gEfhfk0t17gmuyIG/refunds"
                            },
                            "review": None,
                            "shipping": None,
                            "source": None,
                            "source_transfer": None,
                            "statement_descriptor": None,
                            "statement_descriptor_suffix": None,
                            "status": "failed",
                            "transfer_data": None,
                            "transfer_group": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 1,
                    "url": "/v1/charges?payment_intent=pi_3LueggH8gEfhfk0t1APAIgKx"
                },
                "client_secret": "secret",
                "confirmation_method": "automatic",
                "created": 1666195210,
                "currency": "eur",
                "customer": "cus_Mdvs7sdi0PkKz7",
                "description": None,
                "invoice": None,
                "last_payment_error": {
                    "code": "payment_intent_authentication_failure",
                    "decline_code": "generic_decline",
                    "doc_url": "https://stripe.com/docs/error-codes/payment-intent-authentication-failure",
                    "message": "The provided PaymentMethod has failed authentication. You can provide payment_method_data or a new PaymentMethod to attempt to fulfill this PaymentIntent again.",
                    "payment_method": {
                        "id": "pm_1LueghH8gEfhfk0tsqgvAx52",
                        "object": "payment_method",
                        "billing_details": {
                            "address": {
                                "city": None,
                                "country": "BE",
                                "line1": None,
                                "line2": None,
                                "postal_code": None,
                                "state": None
                            },
                            "email": "simon.kepplinger@gmail.com",
                            "name": "Test Test",
                            "phone": None
                        },
                        "created": 1666195211,
                        "customer": None,
                        "livemode": False,
                        "metadata": {},
                        "sofort": {
                            "country": "BE"
                        },
                        "type": "sofort"
                    },
                    "type": "card_error"
                },
                "livemode": False,
                "metadata": {
                    "checkout_params": "{\"product\":\"UHJvZHVjdDo5\",\"stp\":\"g\",\"g\":\"d4z8yn94viml9fryaka\"}",
                    "app_id": "VTV",
                    "redirect_id": "d4z8yn94viml9fryaka",
                    "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1"
                },
                "next_action": None,
                "on_behalf_of": None,
                "payment_method": None,
                "payment_method_options": {
                    "sofort": {
                        "preferred_language": None
                    }
                },
                "payment_method_types": [
                    "sofort"
                ],
                "processing": None,
                "receipt_email": None,
                "review": None,
                "setup_future_usage": None,
                "shipping": None,
                "source": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "requires_payment_method",
                "transfer_data": None,
                "transfer_group": None
            }
        },
        "livemode": False,
        "pending_webhooks": 4,
        "request": {
            "id": None,
            "idempotency_key": None
        },
        "type": "payment_intent.payment_failed"
    })

    return request


@pytest.fixture
def stripe_sofort_fail_instant_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3LuelkH8gEfhfk0t1OeMLo0u",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666195531,
        "data": {
            "object": {
                "id": "pi_3LueggH8gEfhfk0t1APAIgKx",
                "object": "payment_intent",
                "amount": 490,
                "amount_capturable": 0,
                "amount_details": {
                    "tip": {}
                },
                "amount_received": 0,
                "application": None,
                "application_fee_amount": None,
                "automatic_payment_methods": None,
                "canceled_at": None,
                "cancellation_reason": None,
                "capture_method": "automatic",
                "charges": {
                    "object": "list",
                    "data": [],
                    "has_more": False,
                    "total_count": 0,
                    "url": "/v1/charges?payment_intent=pi_3LueggH8gEfhfk0t1APAIgKx"
                },
                "client_secret": "secret",
                "confirmation_method": "automatic",
                "created": 1666195524,
                "currency": "eur",
                "customer": "cus_Mdvs7sdi0PkKz7",
                "description": None,
                "invoice": None,
                "last_payment_error": {
                    "code": "payment_intent_authentication_failure",
                    "doc_url": "https://stripe.com/docs/error-codes/payment-method-customer-decline",
                    "message": "The customer did not approve the PaymentIntent. Provide a new payment method to attempt to fulfill this PaymentIntent again.",
                    "message_code": "payment_intent_redirect_payment_method_failure",
                    "payment_method": {
                        "id": "pm_1LuellH8gEfhfk0t9S5PBw0D",
                        "object": "payment_method",
                        "billing_details": {
                            "address": {
                                "city": None,
                                "country": "BE",
                                "line1": None,
                                "line2": None,
                                "postal_code": None,
                                "state": None
                            },
                            "email": "simon.kepplinger@gmail.com",
                            "name": "Test Test",
                            "phone": None
                        },
                        "created": 1666195525,
                        "customer": None,
                        "livemode": False,
                        "metadata": {},
                        "sofort": {
                            "country": "BE"
                        },
                        "type": "sofort"
                    },
                    "type": "invalid_request_error"
                },
                "livemode": False,
                "metadata": {
                    "checkout_params": "{\"product\":\"UHJvZHVjdDoxMA==\",\"stp\":\"g\",\"g\":\"bxi3pyysn1l9fryaka\"}",
                    "app_id": "VTV",
                    "checkout_token": "5bcb3c53-eca7-456e-91f1-d0263cadf8b1",
                    "redirect_id": "bxi3pyysn1l9fryaka"
                },
                "next_action": None,
                "on_behalf_of": None,
                "payment_method": None,
                "payment_method_options": {
                    "sofort": {
                        "preferred_language": None
                    }
                },
                "payment_method_types": [
                    "sofort"
                ],
                "processing": None,
                "receipt_email": None,
                "review": None,
                "setup_future_usage": None,
                "shipping": None,
                "source": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "requires_payment_method",
                "transfer_data": None,
                "transfer_group": None
            }
        },
        "livemode": False,
        "pending_webhooks": 4,
        "request": {
            "id": None,
            "idempotency_key": "725ad0f4-af5b-4ee4-a614-cf08d8ea27ea"
        },
        "type": "payment_intent.payment_failed"
    })

    return request


@pytest.fixture
def stripe_cc_fail_instant_event():
    request = mock.Mock()
    request.body = json.dumps({
        "id": "evt_3LwQO4H8gEfhfk0t1wXeo8Lo",
        "object": "event",
        "api_version": "2019-12-03",
        "created": 1666616897,
        "data": {
            "object": {
                "id": "pi_3LwQO4H8gEfhfk0t1qSezfR7",
                "object": "payment_intent",
                "amount": 490,
                "amount_capturable": 0,
                "amount_details": {
                    "tip": {}
                },
                "amount_received": 0,
                "application": None,
                "application_fee_amount": None,
                "automatic_payment_methods": None,
                "canceled_at": None,
                "cancellation_reason": None,
                "capture_method": "automatic",
                "charges": {
                    "object": "list",
                    "data": [
                        {
                            "id": "ch_3LwQO4H8gEfhfk0t1TO1ghck",
                            "object": "charge",
                            "amount": 490,
                            "amount_captured": 0,
                            "amount_refunded": 0,
                            "application": None,
                            "application_fee": None,
                            "application_fee_amount": None,
                            "balance_transaction": None,
                            "billing_details": {
                                "address": {
                                    "city": None,
                                    "country": "BE",
                                    "line1": None,
                                    "line2": None,
                                    "postal_code": None,
                                    "state": None
                                },
                                "email": "simon.kepplinger@gmail.com",
                                "name": "Simon Kepplinger",
                                "phone": None
                            },
                            "calculated_statement_descriptor": "ICEHOCKEY LIVESTREAM",
                            "captured": False,
                            "created": 1666616897,
                            "currency": "eur",
                            "customer": "cus_MflvTV6FSeY4HQ",
                            "description": None,
                            "destination": None,
                            "dispute": None,
                            "disputed": False,
                            "failure_balance_transaction": None,
                            "failure_code": "card_declined",
                            "failure_message": "Your card was declined.",
                            "fraud_details": {},
                            "invoice": None,
                            "livemode": False,
                            "metadata": {
                                "channel": "streaming-channel",
                                "payment_id": "UGF5bWVudDox"
                            },
                            "on_behalf_of": None,
                            "order": None,
                            "outcome": {
                                "network_status": "declined_by_network",
                                "reason": "generic_decline",
                                "risk_level": "normal",
                                "risk_score": 40,
                                "seller_message": "The bank did not return any further details with this decline.",
                                "type": "issuer_declined"
                            },
                            "paid": False,
                            "payment_intent": "pi_3LueggH8gEfhfk0t1APAIgKx",
                            "payment_method": "pm_1LwQO2H8gEfhfk0tSh6U1Uj3",
                            "payment_method_details": {
                                "card": {
                                    "brand": "visa",
                                    "checks": {
                                        "address_line1_check": None,
                                        "address_postal_code_check": None,
                                        "cvc_check": "pass"
                                    },
                                    "country": "US",
                                    "exp_month": 2,
                                    "exp_year": 2031,
                                    "fingerprint": "A4vmf1SgFB4XTKmO",
                                    "funding": "credit",
                                    "installments": None,
                                    "last4": "0341",
                                    "mandate": None,
                                    "network": "visa",
                                    "three_d_secure": None,
                                    "wallet": None
                                },
                                "type": "card"
                            },
                            "receipt_email": None,
                            "receipt_number": None,
                            "receipt_url": None,
                            "refunded": False,
                            "refunds": {

                                "object": "list",
                                "data": [],
                                "has_more": False,
                                "total_count": 0,
                                "url": "/v1/charges/ch_3LwQO4H8gEfhfk0t1TO1ghck/refunds"
                            },
                            "review": None,
                            "shipping": None,
                            "source": None,
                            "source_transfer": None,
                            "statement_descriptor": None,
                            "statement_descriptor_suffix": None,
                            "status": "failed",
                            "transfer_data": None,
                            "transfer_group": None
                        }
                    ],
                    "has_more": False,
                    "total_count": 1,
                    "url": "/v1/charges?payment_intent=pi_3LueggH8gEfhfk0t1APAIgKx"
                },
                "client_secret": "pi_3LueggH8gEfhfk0t1APAIgKx_secret_BAxbGbd0ayqhbVYnrwSBF7GgR",
                "confirmation_method": "automatic",
                "created": 1666616896,
                "currency": "eur",
                "customer": "cus_MflvTV6FSeY4HQ",
                "description": None,
                "invoice": None,
                "last_payment_error": {
                    "charge": "ch_3LwQO4H8gEfhfk0t1TO1ghck",
                    "code": "card_declined",
                    "decline_code": "generic_decline",
                    "doc_url": "https://stripe.com/docs/error-codes/card-declined",
                    "message": "Your card was declined.",
                    "payment_method": {
                        "id": "pm_1LwQO2H8gEfhfk0tSh6U1Uj3",
                        "object": "payment_method",
                        "billing_details": {
                            "address": {
                                "city": None,
                                "country": "BE",
                                "line1": None,
                                "line2": None,
                                "postal_code": None,
                                "state": None
                            },
                            "email": "simon.kepplinger@gmail.com",
                            "name": "Simon Kepplinger",
                            "phone": None
                        },
                        "card": {
                            "brand": "visa",
                            "checks": {
                                "address_line1_check": None,
                                "address_postal_code_check": None,
                                "cvc_check": "pass"
                            },
                            "country": "US",
                            "exp_month": 2,
                            "exp_year": 2031,
                            "fingerprint": "A4vmf1SgFB4XTKmO",
                            "funding": "credit",
                            "generated_from": None,
                            "last4": "0341",
                            "networks": {
                                "available": [
                                    "visa"
                                ],
                                "preferred": None
                            },
                            "three_d_secure_usage": {
                                "supported": True
                            },
                            "wallet": None
                        },
                        "created": 1666616895,
                        "customer": None,
                        "livemode": False,
                        "metadata": {},
                        "type": "card"
                    },
                    "type": "card_error"
                },
                "livemode": False,
                "metadata": {
                    "channel": "streaming-channel",
                    "payment_id": "UGF5bWVudDox"
                },
                "next_action": None,
                "on_behalf_of": None,
                "payment_method": None,
                "payment_method_options": {
                    "card": {
                        "installments": None,
                        "mandate_options": None,
                        "network": None,
                        "request_three_d_secure": "automatic"
                    }
                },
                "payment_method_types": [
                    "card"
                ],
                "processing": None,
                "receipt_email": None,
                "review": None,
                "setup_future_usage": None,
                "shipping": None,
                "source": None,
                "statement_descriptor": None,
                "statement_descriptor_suffix": None,
                "status": "requires_payment_method",
                "transfer_data": None,
                "transfer_group": None
            }
        },
        "livemode": False,
        "pending_webhooks": 4,
        "request": {
            "id": "req_l9S2L0Yoq2g5FG",
            "idempotency_key": "875ec26f-1352-4666-af92-52c2929a6998"
        },
        "type": "payment_intent.payment_failed"
    })

    return request
