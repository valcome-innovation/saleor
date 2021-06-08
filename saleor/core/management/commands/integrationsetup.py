from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Factory

from ...utils.random_data import (
    create_address, create_fake_order, get_email, create_channel,
)
from ....account.models import User
from ....discount.utils import fetch_discounts

fake = Factory.create()


class Command(BaseCommand):
    help = "Configure Saleor with integration data"

    def handle(self, *args, **options):
        users = create_unit_test_user(100)
        for user in users:
            self.stdout.write(user.email)

        channel = create_channel("Streaming Channel", "EUR")
        self.stdout.write(channel)


def create_unit_test_user(how_many):
    users = []

    test_user = create_stuff_user(create_address(), "unit", "test", False)
    users.append(test_user)

    discounts = fetch_discounts(timezone.now())
    for _ in range(15):
        create_fake_order(discounts=discounts, customer=test_user)

    for number in range(how_many):
        test_user = create_stuff_user(create_address(), "unit",
                                      "test" + str(number + 1), False)
        users.append(test_user)

    return users


def create_stuff_user(address, first_name, last_name, superuser=False):
    return User.objects.create_user(
        gender="M",
        first_name=first_name,
        last_name=last_name,
        email=get_email(first_name, last_name),
        password="password",
        default_billing_address=address,
        default_shipping_address=address,
        is_staff=True,
        is_active=True,
        is_superuser=superuser,
    )
