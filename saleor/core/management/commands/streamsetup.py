from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from ...utils.random_data import (
    add_address_to_admin,
    create_products_by_schema,
    create_channel, )
from django.contrib.auth.models import Permission
from ...utils.stream_data import (
    create_page,
    create_page_type,
    create_users,
    create_test_user, create_page_translation,
)
from ....account.models import User, Address
from ....account.utils import create_superuser
from ....app.models import App
from ....streaming.models import StreamTicket


class Command(BaseCommand):
    help = "Configure Saleor with minimal data"
    placeholders_dir = "saleor/static/placeholders/"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.tv", "password": "m5$ktVp$3cRv%8DtvR"}
        create_superuser(credentials)

        for msg in create_users(20):
            self.stdout.write(msg)

        self.stdout.write("Creating test user:")
        for msg in create_test_user(100):
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

        self.stdout.write("Creating Apps:")
        self.create_refund_app()

    def create_info_pages(self):
        for msg in create_page_type(1, "Impressum", "about"):
            self.stdout.write(msg)
        for msg in create_page_type(2, "Datenschutzerklärung", "privacy"):
            self.stdout.write(msg)
        for msg in create_page_type(3, "AGB", "terms"):
            self.stdout.write(msg)
        for msg in create_page_type(4, "FAQ", "faq"):
            self.stdout.write(msg)
        for msg in create_page_type(5, "Withdrawal Rights", "withdrawal-rights"):
            self.stdout.write(msg)

        about = create_page(1, "Impressum", "about")
        privacy = create_page(2, "Datenschutzerklärung", "privacy")
        terms = create_page(3, "AGB", "terms")
        faq = create_page(4, "Frequently Asked Questions", "faq")
        withdrawal = create_page(5, "Withdrawal Rights", "withdrawal-rights")

        self.stdout.write(about.slug)
        self.stdout.write(privacy.slug)
        self.stdout.write(terms.slug)
        self.stdout.write(faq.slug)
        self.stdout.write(withdrawal.slug)

        for msg in create_page_translation(about):
            self.stdout.write(msg)
        for msg in create_page_translation(privacy):
            self.stdout.write(msg)
        for msg in create_page_translation(terms):
            self.stdout.write(msg)
        for msg in create_page_translation(faq):
            self.stdout.write(msg)
        for msg in create_page_translation(withdrawal):
            self.stdout.write(msg)

    def create_stream_ticket(self, user):
        stream_ticket = StreamTicket()
        stream_ticket.game_id = 1
        stream_ticket.user = user
        stream_ticket.stream_type = 'Game'
        stream_ticket.game_id = "14"
        stream_ticket.season_id = None
        stream_ticket.team_ids = None
        stream_ticket.expires = None
        stream_ticket.type = "single"
        stream_ticket.product_slug = "single"
        stream_ticket.save()
        return stream_ticket

    def create_company_address(self):
        company_address = Address(
            company_name="Valcome Innovation GmbH",
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

    def create_refund_app(self):
        manage_order_permissions = Permission.objects.filter(
            codename='manage_orders'
        ).first()

        app, _ = App.objects.get_or_create(
            name="Live Server Refund",
        )

        app.permissions.set([manage_order_permissions])

        if app.tokens.all().count() == 0:
            app.tokens.create(
                name="Management Refund Token",
                auth_token="DEV_REFUND_TOKEN_30_CHARACTERS"
            )

        print(f"App: {app.name}")
