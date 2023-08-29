import logging
import jwt
import django.conf as conf
from django.middleware.csrf import _get_new_csrf_token
from promise import Promise, is_thenable
from django.utils import timezone
from django.core.exceptions import ValidationError
from social_django.utils import load_strategy, load_backend
from social_django.compat import reverse
from django.utils.crypto import get_random_string

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
    email = context.backend.do_auth(access_token)

    if hasattr(context, 'user'):
        context.user = email

    return do_authenticate(email)


def validate_social_auth_config():
    if conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is None or conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is None:
        raise ValidationError(code=AccountErrorCode.CHANNEL_INACTIVE.value,
                              message="Google Authentication not configured")
    elif conf.settings.SOCIAL_AUTH_FACEBOOK_KEY is None or conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET is None:
        raise ValidationError(code=AccountErrorCode.CHANNEL_INACTIVE.value,
                              message="Facebook Authentication not configured")


def validate_user_email(user_data):
    if not user_data or not ("email" in user_data and user_data["email"].strip()):
        raise ValidationError({
            "email": ValidationError(
                "There is no email address associated with your social account.",
                code=AccountErrorCode.INVALID_CREDENTIALS,
            )
        })


def do_authenticate(email):
    user = User.objects.filter(email=email).first()

    # VALCOME error handling (same as CreateToken)
    if not user.is_active and not user.last_login:
        raise ValidationError({
            "email": ValidationError(
                "Account needs to be confirmed via email.",
                code=AccountErrorCode.ACCOUNT_NOT_CONFIRMED.value,
            )
        })

    # VALCOME error handling (same as CreateToken)
    if not user.is_active and user.last_login:
        raise ValidationError({
            "email": ValidationError(
                "Account inactive.",
                code=AccountErrorCode.INACTIVE.value,
            )
        })

    try:
        user.jwt_token_key = get_random_string()  # VALCOME user logout
        access_token = jwt.create_access_token(user)
        csrf_token = _get_new_csrf_token()
        refresh_token = jwt.create_refresh_token(user, {"csrfToken": csrf_token})

        User.objects.filter(email=user.email).update(
            jwt_token_key=user.jwt_token_key
        )

        return ExternalAccessTokens(
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
    except BaseException as e:
        print(e)
        raise ValidationError(str(e), code=AccountErrorCode.GRAPHQL_ERROR)


def on_resolve(values):
    user, payload = values
    csrf_token = _get_new_csrf_token()
    payload.token = jwt.create_access_token(user)
    payload.refresh_token = jwt.create_refresh_token(user, {"csrfToken": csrf_token})
    return payload
