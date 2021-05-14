import graphene

from saleor.account import models
from saleor.account.models import User
from saleor.graphql.core.mutations import ModelMutation
from saleor.graphql.core.types.common import AccountError


class AccountFavoriteTeamUpdate(ModelMutation):
    user = graphene.Field(
        User, description="A user instance for which the ticket was created."
    )

    class Arguments:
        favorite_team = graphene.String(
            description="The users favorite team ID", required=False
        )

    class Meta:
        description = "Update the favorite team of the user"
        model = models.User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        user.favorite_team = data.get("favorite_team", None)
        user.save(update_fields=["favorite_team"])
        return AccountFavoriteTeamUpdate(user=user)
