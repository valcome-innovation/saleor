import graphene


class SofortPaymentMeta(graphene.ObjectType):
    gateway = graphene.Field(
        graphene.String,
        description="A gateway to use with that payment.",
        required=True,
    )
    checkout_token = graphene.String(
        required=True,
        description=(
            "Checkout token"
        ),
    )
    checkout_params = graphene.String(
        required=True,
        description=(
            "Checkout params"
        ),
    )
    redirect_id = graphene.String(
        required=False,
        description=(
            "Redirect ID"
        ),
    )
