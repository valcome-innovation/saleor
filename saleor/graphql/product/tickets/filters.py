import graphene
from django.core.exceptions import ValidationError

from ..filters import filter_attributes
from ....graphql.core.filters import MetadataFilterBase, ListObjectTypeFilter
from ....graphql.core.types import ChannelFilterInputObjectType
from ....product.models import Product


class TicketProductFilter(MetadataFilterBase):
    stream_type = ListObjectTypeFilter(
        input_class=graphene.String, method="pass_through",
    )
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
            "stream_type",
            "teams",
            "leagues",
            "single_teams",
        ]

    @property
    def qs(self):
        teams = self.get_from_data("teams")
        leagues = self.get_from_data("leagues")
        single_teams = self.get_from_data("single_teams")

        single_filter = self.get_single_filter(single_teams)
        season_filter = self.get_season_filter(teams)
        timed_season_filter = self.get_timed_season_filter(teams)
        timed_filter = self.get_timed_filter(teams, leagues)

        attributes_filter = single_filter \
                            | timed_season_filter \
                            | season_filter \
                            | timed_filter

        return super().qs & attributes_filter

    def get_from_data(self, key):
        data = self.data.get(key)
        if not data:
            raise ValidationError('Missing filter attribute: ' + key)
        return [value.lower() for value in data]

    def get_single_filter(self, single_teams):
        stream_type_filter = self.get_stream_type_filter()
        type_filter = self.get_ticket_type_filter("single")
        attribute_filter = self.get_attribute_filter("teams", single_teams)

        return type_filter & stream_type_filter & attribute_filter

    def get_timed_filter(self, teams, leagues):
        stream_type_filter = self.get_stream_type_filter()
        type_filter = self.get_ticket_type_filter("timed")
        teams_filter = self.get_attribute_filter("teams", teams)
        attribute_filter = self.get_attribute_filter("leagues", leagues)

        return type_filter & stream_type_filter & teams_filter & attribute_filter

    def get_timed_season_filter(self, teams):
        stream_type_filter = self.get_stream_type_filter()
        type_filter = self.get_ticket_type_filter("timed-season")
        teams_filter = self.get_attribute_filter("teams", teams)

        return type_filter & stream_type_filter & teams_filter

    def get_season_filter(self, teams):
        stream_type_filter = self.get_stream_type_filter()
        type_filter = self.get_ticket_type_filter("season")
        teams_filter = self.get_attribute_filter("teams", teams)

        return type_filter & stream_type_filter & teams_filter

    def get_stream_type_filter(self):
        stream_type = self.get_from_data("stream_type")

        return self.get_attribute_filter("stream-type", stream_type)

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
