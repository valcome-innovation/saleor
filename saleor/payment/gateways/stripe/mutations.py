import graphene
from stripe.api_resources.payment_method import PaymentMethod

from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.types.common import StripeError
from saleor.payment.gateways.stripe.exceptions import StripeException
from saleor.payment.gateways.stripe.plugin import StripeGatewayPlugin
from saleor.plugins import manager


class StripePaymentSourceDelete(BaseMutation):
    payment_method_id = graphene.String(
        required=True,
        description="The payment method that got deleted",
    )

    class Arguments:
        id = graphene.String(
            required=True, description="ID of the payment method to delete."
        )

    class Meta:
        description = "Deletes a stored payment method of a customer."
        error_type_class = StripeError
        error_type_field = "stripe_errors"

    @classmethod
    def check_permissions(cls, context, permissions=None):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        stripe_plugin = manager.get_plugins_manager().get_plugin("saleor.payments.stripe")

        if isinstance(stripe_plugin, StripeGatewayPlugin):
            payment_method, error = stripe_plugin.delete_payment_source(
                payment_method_id=data.get("id")
            )

            if error:
                raise StripeException()

            return StripePaymentSourceDelete(
                payment_method_id=payment_method.id
            )
