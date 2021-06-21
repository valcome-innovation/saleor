import graphene
from django.db.models import QuerySet

from ..filters import filter_attributes
from ....graphql.core.filters import MetadataFilterBase, ListObjectTypeFilter
from ....graphql.core.types import ChannelFilterInputObjectType
from ....product.models import Product


class TicketProductFilter(MetadataFilterBase):
    teams = ListObjectTypeFilter(
        input_class=graphene.String, method="pass_through",
    )
    leagues = ListObjectTypeFilter(
        input_class=graphene.String, method="pass_through",
     )
    single_teams = ListObjectTypeFilter(
        input_class=graphene.String, method="pass_through",
    )

    class Meta:
        model = Product
        fields = [
            "teams",
            "leagues",
            "single_teams",
        ]

    @property
    def qs(self):
        teams = self.data.get("teams") or []
        leagues = self.data.get("leagues") or []
        single_teams = self.data.get("single_teams") or []

        single_filter = self.get_single_filter(single_teams)
        day_filter = self.get_day_filter(leagues)
        month_filter = self.get_month_filter(teams, leagues)
        season_filter = self.get_season_filter(teams)

        attributes_filter = single_filter | day_filter | month_filter | season_filter

        final_qs = super().qs & attributes_filter
        print(final_qs.query)
        return final_qs

    def get_single_filter(self, single_teams):
        type_filter = self.get_ticket_type_filter("single")
        attribute_filter = self.get_attribute_filter("teams", single_teams)
        return type_filter & attribute_filter

    def get_day_filter(self, leagues):
        type_filter = self.get_ticket_type_filter("day")
        attribute_filter = self.get_attribute_filter("leagues", leagues)
        return type_filter & attribute_filter

    def get_month_filter(self, teams, leagues):
        type_filter = self.get_ticket_type_filter("month")
        teams_filter = self.get_attribute_filter("teams", teams)
        leagues_filter = self.get_attribute_filter("leagues", leagues)
        return type_filter & teams_filter & leagues_filter

    def get_season_filter(self, teams):
        type_filter = self.get_ticket_type_filter("season")
        teams_filter = self.get_attribute_filter("teams", teams)
        empty_filter = self.get_attribute_filter("teams", []) # TODO: find solution for empty attributes value
        return type_filter & (teams_filter | empty_filter)

    def get_ticket_type_filter(self, ticket_type: "str"):
        attribute = self.get_attribute_data('ticket-type', [ticket_type])
        return filter_attributes(Product.objects.all(), None, attribute)

    def get_attribute_filter(self, slug, values):
        attribute = self.get_attribute_data(slug, values)
        return filter_attributes(Product.objects.all(), None, attribute)

    def get_attribute_data(self, slug, values):
        return [{"slug": slug, "values": values}]

    def pass_through(self, queryset, name, value):
        return queryset


class TicketProductFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = TicketProductFilter
