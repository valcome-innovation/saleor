from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.utils import create_superuser
from ....account.models import User
from ....core.utils import create_thumbnails
from ...utils.random_data import (
    add_address_to_admin
)


def create_user(credentials):
    user, created = User.objects.get_or_create(
        email=credentials["email"],
        defaults={"is_active": True, "is_staff": False, "is_superuser": False},
    )
    if created:
        user.set_password(credentials["password"])
        user.save()
        create_thumbnails(
            pk=user.pk, model=User, size_set="user_avatars", image_attr="avatar"
        )
        msg = "User - %(email)s/%(password)s" % credentials
    else:
        msg = "User already exists - %(email)s" % credentials
    return msg


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
