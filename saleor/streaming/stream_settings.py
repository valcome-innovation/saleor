import os
import ast
import os.path
from get_docker_secret import get_docker_secret


def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError("{} is an invalid value for {}".format(value, name)) from e
    return default_value


def get_aws_email_url(email_url):
    AWS_SMTP_USER = get_docker_secret("aws_smtp_user", secrets_dir="/run/secrets")
    AWS_SMTP_PASSWORD = get_docker_secret("aws_smtp_password", secrets_dir="/run/secrets")

    if not email_url and AWS_SMTP_USER and AWS_SMTP_PASSWORD:
        return "smtp://%s:%s@email-smtp.eu-central-1.amazonaws.com:587/?tls=True" % (
            AWS_SMTP_USER, AWS_SMTP_PASSWORD,
        )
    else:
        return email_url


def setup_database_url():
    DB_USER = get_docker_secret('saleor_db_user', secrets_dir="/run/secrets")
    DB_PASSWORD = get_docker_secret('saleor_db_password', secrets_dir="/run/secrets")
    DB_HOST = os.environ.get("DB_HOST")
    DB_NAME = os.environ.get("DB_NAME")

    if DB_PASSWORD is not None and DB_USER is not None and DB_NAME is not None and DB_HOST is not None:
        os.environ['DATABASE_URL'] =  "postgres://%s:%s@%s/%s" % (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)


def add_middlewares(middlewares):
    middlewares.append("django.contrib.sessions.middleware.SessionMiddleware")


def add_apps(installed_apps):
    installed_apps.append("social_django")
    installed_apps.append("saleor.streaming")


def add_backends(backends):
    backends.append("social_core.backends.google.GoogleOAuth2")
    backends.append("social_core.backends.facebook.FacebookOAuth2")


def add_plugins(plugins):
    plugins.append("saleor.plugins.user_email.plugin.UserEmailPlugin")
    plugins.append("saleor.payment.gateways.paypal.plugin.PaypalGatewayPlugin")
    plugins.append("saleor.payment.gateways.sofort.plugin.SofortGatewayPlugin")
    plugins.append("saleor.plugins.streaming.plugin.StreamingPlugin")
    plugins.append("saleor.plugins.social_auth.plugin.SocialAuthPlugin")


SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", None)

APP_ID = os.environ.get("APP_ID", None)
AWS_KINESIS_STREAM_NAME = os.environ.get("AWS_KINESIS_STREAM_NAME", None)
DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY")

# Social Auth
SOCIAL_PLUGIN_ACTIVE = get_bool_from_env("STRIPE_PLUGIN_ACTIVE", False)

# Stripe
STRIPE_PLUGIN_ACTIVE = get_bool_from_env("STRIPE_PLUGIN_ACTIVE", False)
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", None)
STRIPE_PRIVATE_KEY = os.environ.get("STRIPE_PRIVATE_KEY", None)
STRIPE_STATEMENT_DESCRIPTOR = os.environ.get("STRIPE_STATEMENT_DESCRIPTOR", None)

# PayPal
PAYPAL_PLUGIN_ACTIVE = get_bool_from_env("PAYPAL_PLUGIN_ACTIVE", False)
PAYPAL_PUBLIC_KEY = os.environ.get("PAYPAL_PUBLIC_KEY", None)
PAYPAL_PRIVATE_KEY = os.environ.get("PAYPAL_PRIVATE_KEY", None)

# Vatlayer
VATLAYER_PLUGIN_ACTIVE = get_bool_from_env("VATLAYER_PLUGIN_ACTIVE", False)
VATLAYER_ACCESS_KEY = os.environ.get("VATLAYER_ACCESS_KEY", None)
