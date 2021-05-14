import django.conf as conf
from io import StringIO
from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.models import StreamTicket, User
from ....account.utils import create_superuser
from ....site.models import AuthenticationBackends
from ...utils.random_data import (
    add_address_to_admin,
    create_users,
    create_products_by_schema
)
from ...utils.stream_data import (
    create_page
)


class Command(BaseCommand):
    help = "Configure Salor with minimal data"
    placeholders_dir = "saleor/static/placeholders/"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.tv", "password": "m5$ktVp$3cRv%8DtvR"}
        create_superuser(credentials)

        user = User.objects.filter(email="dev@valcome.tv").first()
        self.create_stream_ticket(user)

        add_address_to_admin(credentials["email"])
        self.create_info_pages()
        self.create_auth_keys()
        self.create_app_with_token()
        create_products_by_schema(placeholder_dir=self.placeholders_dir,
                                  create_images=False,
                                  data_json="streamdb_data.json")


    def create_info_pages(self):
        for msg in create_page("Impressum", "about"):
            self.stdout.write(msg)
        for msg in create_page("Datenschutzerklärung", "privacy"):
            self.stdout.write(msg)
        for msg in create_page("AGB", "terms"):
            self.stdout.write(msg)

    def create_stream_ticket(self, user):
        stream_ticket = StreamTicket()
        stream_ticket.user = user
        stream_ticket.game_id = "14"
        stream_ticket.season_id = "3"
        stream_ticket.team_id = "6"
        stream_ticket.expires = None
        stream_ticket.type = "single"
        stream_ticket.save()
        return stream_ticket
