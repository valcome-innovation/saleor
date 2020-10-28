import graphene
import logging
import jwt
from datetime import datetime
from functools import wraps

from django.utils.translation import ugettext as _
import django.conf as conf

from promise import Promise, is_thenable
from django.dispatch import Signal
from django.utils import timezone


token_issued = Signal(providing_args=['request', 'user'])

from graphql_jwt.exceptions import JSONWebTokenError
from graphql_jwt.mixins import ResolveMixin, ObtainJSONWebTokenMixin
from graphql_jwt.decorators import setup_jwt_cookie
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token
from graphql_jwt.refresh_token.shortcuts import refresh_token_lazy
from social_django.utils import load_strategy, load_backend
from social_django.compat import reverse

from ..types import User
from ...core.types import Error
from ....site.models import AuthorizationKey

LOG = logging.getLogger(__name__)

def token_auth(f):
    @wraps(f)
    @setup_jwt_cookie
    def wrapper(cls, root, info, **kwargs):
        context = info.context
        context._jwt_token_auth = True

        def on_resolve(values):
            user, payload = values
            payload.token = get_token(user, context)

            if jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
                payload.refresh_token = refresh_token_lazy(user)

            return payload

        token = kwargs.get('access_token')
        backend = kwargs.get('backend')

        if conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is None or conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is None:
            authorization_key = AuthorizationKey.objects.get(name="google-oauth2")
            conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = authorization_key.key
            conf.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = authorization_key.password

        if conf.settings.SOCIAL_AUTH_FACEBOOK_KEY is None or conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET is None:
            authorization_key = AuthorizationKey.objects.get(name="facebook")
            conf.settings.SOCIAL_AUTH_FACEBOOK_KEY = authorization_key.key
            conf.settings.SOCIAL_AUTH_FACEBOOK_SECRET = authorization_key.password

        context.social_strategy = load_strategy(context)

        # backward compatibility in attribute name, only if not already
        # defined
        if not hasattr(context, 'strategy'):
            context.strategy = context.social_strategy
        uri = reverse('social:complete', args=(backend,))
        context.backend = load_backend(context.social_strategy, backend, uri)

        user_data = context.backend.user_data(token)

        if not user_data or not (user_data["email"] and user_data["email"].strip()):
            LOG.error('Empty email or id from social login received')
            LOG.error(user_data)
            raise JSONWebTokenError(_('Please, enter valid credentials'))

        user = context.backend.do_auth(token)

        if hasattr(context, 'user'):
            context.user = user

        result = f(cls, root, info, **kwargs)
        values = (user, result)

        token_issued.send(sender=cls, request=context, user=user)

        if is_thenable(result):
            return Promise.resolve(values).then(on_resolve)
        return on_resolve(values)
    return wrapper


class JSONWebTokenMutation(ObtainJSONWebTokenMixin, graphene.Mutation):
    class Meta:
        abstract = True

    @classmethod
    @token_auth
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)


class CreateOAuthToken(ResolveMixin, JSONWebTokenMutation):
    errors = graphene.List(Error, required=True)
    user = graphene.Field(User)

    class Arguments:
        access_token = graphene.String(description="Access token.")
        backend = graphene.String(description="Authenticate backend")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            result = super().mutate(root, info, **kwargs)
        except JSONWebTokenError as e:
            print(e)
            return CreateOAuthToken(errors=[Error(message=str(e))])
        else:
            decodedToken = jwt.decode(result.token, None, None)
            user = result.user
            user.last_jwt_iat = datetime.fromtimestamp(decodedToken['origIat'], tz=timezone.utc)
            user.save(update_fields=["last_jwt_iat"])
            return result

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user, errors=[])


class OAuthMutations(graphene.ObjectType):
    oauth_token_create = CreateOAuthToken.Field()
