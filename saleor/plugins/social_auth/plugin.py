import logging

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.dispatch import Signal
import django.conf as conf

from .oauth2 import social_auth
from ..base_plugin import BasePlugin, ConfigurationTypeField, ExternalAccessTokens
from ..models import PluginConfiguration
from ... import settings
from ...streaming import stream_settings

logger = logging.getLogger(__name__)
token_issued = Signal(providing_args=['request', 'user'])


class SocialAuthPlugin(BasePlugin):

    PLUGIN_ID = "valcome.social_auth"
    PLUGIN_NAME = "Social Authentication"
    DEFAULT_ACTIVE = stream_settings.SOCIAL_PLUGIN_ACTIVE
    PLUGIN_DESCRIPTION = (
        "Enables social authentication options via Google and Facebook"
    )
    DEFAULT_CONFIGURATION = [
        {"name": "Google Client Key", "value": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY},
        {"name": "Google Secret", "value": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET},
        {"name": "Facebook App-ID", "value": settings.SOCIAL_AUTH_FACEBOOK_KEY},
        {"name": "Facebook App Secret", "value": settings.SOCIAL_AUTH_FACEBOOK_SECRET},
    ]

    CONFIG_STRUCTURE = {
        "Google Client Key": {
            "type": ConfigurationTypeField.STRING,
            "help_test": (
                "Google Client Key"
            ),
            "label": "Google Client Key",
        },
        "Google Secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_test": (
                "Google Secret"
            ),
            "label": "Google Secret",
        },
        "Facebook App-ID": {
            "type": ConfigurationTypeField.STRING,
            "help_test": (
                "Facebook App-ID"
            ),
            "label": "Facebook App-ID",
        },
        "Facebook App Secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_test": (
                "Facebook App Secret"
            ),
            "label": "Facebook App Secret",
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        config = { item["name"]: item["value"] for item in plugin_configuration.configuration }
        google_config = config["Google Client Key"] and config["Google Secret"]
        facebook_config = config["Facebook App-ID"] and config["Facebook App Secret"]

        if plugin_configuration.active and (not google_config and not facebook_config):
            raise ValidationError(message="You have to at least configre a single auth provider.")

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        if self.active:
            self.update_social_auth_settings()
            result = social_auth(data["backend"], data["access_token"], request)
            token_issued.send(sender=self, request=request, user=result.user)
            return result
        else:
            raise ValidationError(message="The social auth plugin is not configured correctly.")

    def update_social_auth_settings(self):
        if conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is None or conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is None:
            conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = self.get_config_value("Google Client Key")
            conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = self.get_config_value("Google Secret")

        if conf.settings.SOCIAL_AUTH_FACEBOOK_KEY is None or conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET is None:
            conf.settings.SOCIAL_AUTH_FACEBOOK_KEY = self.get_config_value("Facebook App-ID")
            conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET = self.get_config_value("Facebook App Secret")

    def get_configuration(self):
        return { item["name"]: item["value"] for item in self.configuration }

    def get_config_value(self, key):
        return self.get_configuration()[key]
