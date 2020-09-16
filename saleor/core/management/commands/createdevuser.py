from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.utils import create_superuser, create_user
from ...utils.random_data import (
    add_address_to_admin
)


class Command(BaseCommand):
    help = "Create DEV user for testing"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.at", "password": "passwerd"}
        msg = create_superuser(credentials)
        self.stdout.write(msg)
        add_address_to_admin(credentials["email"])

        msg = create_user({"email": "free@mail.com", "password": "passwerd"})
        self.stdout.write(msg)

        msg = create_user({"email": "season@mail.com", "password": "passwerd"})
        self.stdout.write(msg)



