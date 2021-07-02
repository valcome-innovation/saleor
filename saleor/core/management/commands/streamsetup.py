import django.conf as conf
from io import StringIO
from django.apps import apps
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.models import User, Address
from ....streaming.models import StreamTicket
from ....account.utils import create_superuser
from ....site.models import AuthenticationBackends
from ...utils.random_data import (
    add_address_to_admin,
    create_products_by_schema,
    create_channel, create_address,
)
from ...utils.stream_data import (
    create_page,
    create_page_type,
    create_users
)


class Command(BaseCommand):
    help = "Configure Saleor with minimal data"
    placeholders_dir = "saleor/static/placeholders/"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.tv", "password": "m5$ktVp$3cRv%8DtvR"}
        create_superuser(credentials)

        for msg in create_users(20):
            self.stdout.write(msg)

        user = User.objects.filter(email="dev@valcome.tv").first()
        self.create_stream_ticket(user)

        add_address_to_admin(credentials["email"])

        self.create_info_pages()

        channel = create_channel("Streaming Channel", "EUR")
        self.stdout.write(channel)

        self.create_company_address()

        create_products_by_schema(placeholder_dir=self.placeholders_dir,
                                  create_images=False,
                                  data_json="streamdb_data.json")

    def create_info_pages(self):
        for msg in create_page_type(1, "Impressum", "about"):
            self.stdout.write(msg)
        for msg in create_page_type(2, "Datenschutzerklärung", "privacy"):
            self.stdout.write(msg)
        for msg in create_page_type(3, "AGB", "terms"):
            self.stdout.write(msg)

        for msg in create_page(1, "Impressum", "about"):
            self.stdout.write(msg)
        for msg in create_page(2, "Datenschutzerklärung", "privacy"):
            self.stdout.write(msg)
        for msg in create_page(3, "AGB", "terms"):
            self.stdout.write(msg)

    def create_stream_ticket(self, user):
        stream_ticket = StreamTicket()
        stream_ticket.user = user
        stream_ticket.game_id = "14"
        stream_ticket.season_id = None
        stream_ticket.team_ids = None
        stream_ticket.expires = None
        stream_ticket.type = "single"
        stream_ticket.save()
        return stream_ticket

    def create_company_address(self):
        company_address = Address(
            company_name="Valcome Analytics GmbH",
            street_address_1="Im Backerfeld 12a",
            city="Linz",
            postal_code="4020",
            country="AT",
            country_area="OOE"
        )
        company_address.save()

        site_settings = Site.objects.get_current().settings
        site_settings.company_address = company_address
        site_settings.save(update_fields=["company_address"])
