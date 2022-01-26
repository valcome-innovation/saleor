import graphene

from .resolvers import resolve_payment_meta


class SofortQueries(graphene.ObjectType):
    payment_meta = graphene.String(
        description="Look up a payment meta by payment intent ID",
        id=graphene.Argument(
            graphene.ID, description="ID of the payment intent", required=True
        )
    )

    def resolve_payment_meta(self, info, **data):
        return resolve_payment_meta(data.get("id"))
