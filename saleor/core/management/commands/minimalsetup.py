import django.conf as conf
from io import StringIO
from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.utils import create_superuser
from ....site.models import AuthenticationBackends
from ...utils.random_data import (
    add_address_to_admin,
    create_auth_key,
    create_app_with_token
)

class Command(BaseCommand):
    help = "Configure Salor with minimal data"

    def handle(self, *args, **options):
        credentials = {"email": "dev@valcome.at", "password": "passwerd"}
        msg = create_superuser(credentials)
        self.stdout.write(msg)
        add_address_to_admin(credentials["email"])

        msg = create_auth_key(AuthenticationBackends.GOOGLE,
                        conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                        conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET)
        self.stdout.write(msg)

        msg = create_auth_key(AuthenticationBackends.FACEBOOK,
                        conf.settings.SOCIAL_AUTH_FACEBOOK_KEY,
                        conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET)
        self.stdout.write(msg)

        msg = create_app_with_token(conf.settings.APP_NAME, conf.settings.APP_TOKEN)
        self.stdout.write(msg)
