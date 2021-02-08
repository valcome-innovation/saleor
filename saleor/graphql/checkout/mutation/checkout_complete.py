from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch

from ...core.mutations import BaseMutation
from ....account.error_codes import AccountErrorCode
from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.utils import (
    abort_order_data,
    create_order,
    prepare_order_data,
)

from ....core import analytics
from ....core.exceptions import InsufficientStock
from ....core.taxes import TaxError
from ....core.utils.url import validate_storefront_url
from ....discount import models as voucher_model
from ....graphql.checkout.utils import clean_checkout_payment, clean_checkout_shipping
from ....order.models import Order
from ....payment import PaymentError, gateway, models as payment_models
from ....payment.interface import AddressData
from ....payment.models import Payment, Transaction
from ....payment.utils import store_customer_id
from ..types import Checkout


def do_complete_checkout(cls: BaseMutation, info, checkout_id: str, store_source: bool, data):
    checkout = retrieve_checkout_or_error(cls, info, checkout_id)
    lines = list(checkout)
    discounts = info.context.discounts
    user = info.context.user

    clean_checkout_shipping(checkout, lines, discounts, CheckoutErrorCode)
    clean_checkout_payment(checkout, lines, discounts, CheckoutErrorCode)

    payment = checkout.get_last_active_payment()
    order_data = do_prepare_order_data_transactional(checkout, lines, info, discounts)

    billing_address = get_billing_address(order_data)
    shipping_address = get_shipping_address(order_data)

    redirect_url = data.get("redirect_url", "")
    if redirect_url:
        validate_redirect_url(redirect_url)

    txn = execute_payment_transaction(payment, order_data, store_source, redirect_url)

    if txn.customer_id and user.is_authenticated:
        store_customer_id(user, payment.gateway, txn.customer_id)

    if not txn.action_required:
        order = create_order_and_delete_checkout(checkout, order_data, user, redirect_url)
    else:
        order = None

    return order, txn.action_required, get_next_action(txn)


def retrieve_checkout_or_error(cls: BaseMutation, info, checkout_id: str):
    return cls.get_node_or_error(
        info=info,
        node_id=checkout_id,
        field="checkout_id",
        only_type=Checkout,
        qs=models.Checkout.objects.prefetch_related(
            "gift_cards",
            "lines",
            Prefetch(
                "payments",
                queryset=payment_models.Payment.objects.prefetch_related("order", "order__lines"),
            ),
        ).select_related("shipping_method", "shipping_method__shipping_zone"),
    )


def do_prepare_order_data_transactional(checkout, lines, info, discounts):
    with transaction.atomic():
        try:
            return prepare_order_data(
                checkout=checkout,
                lines=lines,
                tracking_code=analytics.get_client_id(info.context),
                discounts=discounts,
            )
        except InsufficientStock as e:
            raise ValidationError(f"Insufficient product stock: {e.item}", code=e.code)
        except voucher_model.NotApplicable:
            raise ValidationError(
                "Voucher not applicable",
                code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE)
        except TaxError as tax_error:
            raise ValidationError(
                "Unable to calculate taxes - %s" % str(tax_error),
                code=CheckoutErrorCode.TAX_ERROR )


def get_billing_address(order_data):
    billing_address = order_data["billing_address"]
    return AddressData(**billing_address.as_data())


def get_shipping_address(order_data):
    shipping_address = order_data.get("shipping_address", None)

    if shipping_address is not None:
        shipping_address = AddressData(**shipping_address.as_data())

    return shipping_address


def execute_payment_transaction(payment: Payment, order_data, store_source: bool, return_url: str = None):
    try:
        if payment.to_confirm:
            txn = gateway.confirm(payment)
        else:
            txn = gateway.process_payment(
                payment=payment,
                token=payment.token,
                payment_intent=payment.payment_intent,
                store_source=store_source,
                return_url=return_url
            )

        if txn.is_success:
            return txn
        else:
            raise PaymentError(txn.error)

    except PaymentError as e:
        abort_order_data(order_data)
        raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR)


def validate_redirect_url(redirect_url):
    if redirect_url:
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID
            )


def create_order_and_delete_checkout(checkout, order_data, user, redirect_url):
    order = create_order(
        checkout=checkout,
        order_data=order_data,
        user=user,
        redirect_url=redirect_url,
    )
    checkout.delete()
    return order


def get_next_action(txn: Transaction) -> Optional[str]:
    if "next_action" in txn.gateway_response:
        return txn.gateway_response.next_action
