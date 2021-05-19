import logging
import jwt
import django.conf as conf
from django.middleware.csrf import _get_new_csrf_token
from promise import Promise, is_thenable
from django.utils import timezone
from django.core.exceptions import ValidationError
from social_django.utils import load_strategy, load_backend
from social_django.compat import reverse

from ..base_plugin import ExternalAccessTokens
from ...core import jwt
from ...graphql.account.mutations.authentication import ExternalObtainAccessTokens
from ...graphql.core.types.common import AccountError
from ...account.error_codes import AccountErrorCode
from ...account.models import User

LOG = logging.getLogger(__name__)


def social_auth(backend, access_token, context) -> ExternalAccessTokens:
    context._jwt_token_auth = True

    validate_social_auth_config()
    context.social_strategy = load_strategy(context)

    # backward compatibility in attribute name, only if not already defined
    if not hasattr(context, 'strategy'):
        context.strategy = context.social_strategy

    uri = reverse('social:complete', args=(backend,))
    context.backend = load_backend(context.social_strategy, backend, uri)
    user_data = context.backend.user_data(access_token)
    validate_user_email(user_data)
    user = context.backend.do_auth(access_token)

    if hasattr(context, 'user'):
        context.user = user

    return do_authenticate(user)


def validate_social_auth_config():
    if conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is None or conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is None:
        raise ValidationError(code=AccountErrorCode.CHANNEL_INACTIVE.value,
                              message="Google Authentication not configured")
    elif conf.settings.SOCIAL_AUTH_FACEBOOK_KEY is None or conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET is None:
        raise ValidationError(code=AccountErrorCode.CHANNEL_INACTIVE.value,
                              message="Facebook Authentication not configured")


def validate_user_email(user_data):
    if not user_data or not (user_data["email"] and user_data["email"].strip()):
        LOG.error('Empty email from social login received')
        LOG.error(user_data)
        raise ValidationError(code=AccountErrorCode.INVALID_CREDENTIALS.value,
                              message="Invalid Email", )


def do_authenticate(email):
    try:
        user = User.objects.filter(email=email, is_active=True).first()
        access_token = jwt.create_access_token(user)
        csrf_token = _get_new_csrf_token()
        refresh_token = jwt.create_refresh_token(user, {"csrfToken": csrf_token})
        return ExternalAccessTokens(
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
    except BaseException as e:
        print(e)
        return ExternalObtainAccessTokens(errors=[
            AccountError(code=AccountErrorCode.GRAPHQL_ERROR, message=str(e))
        ])


def on_resolve(values):
    user, payload = values
    csrf_token = _get_new_csrf_token()
    payload.token = jwt.create_access_token(user)
    payload.refresh_token = jwt.create_refresh_token(user, {"csrfToken": csrf_token})
    return payload
