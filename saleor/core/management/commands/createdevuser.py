from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.utils import create_superuser
from ...utils.random_data import (
    add_address_to_admin
)

class Command(BaseCommand):
    help = "Create dev user for testing"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.at", "password": "passwerd"}
        msg = create_superuser(credentials)
        self.stdout.write(msg)
        add_address_to_admin(credentials["email"])

