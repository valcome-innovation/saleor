from typing import Optional

import opentracing
import opentracing.tags
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from django.utils import timezone
from graphql import ResolveInfo
from graphql_jwt.middleware import JSONWebTokenMiddleware
from graphql_jwt.exceptions import JSONWebTokenError
from graphql_jwt.utils import get_http_authorization, jwt_decode
from graphql_jwt.settings import jwt_settings

from .account.mutations.base import INVALID_TOKEN
from ..account.models import User
from ..app.models import App
from ..core.exceptions import ReadOnlyException
from ..core.tracing import should_trace
from .views import API_PATH, GraphQLView


class JWTMiddleware(JSONWebTokenMiddleware):
    def resolve(self, next, root, info, **kwargs):
        request = info.context

        if needs_live_client_jwt_verification(request):
            token = get_live_client_authorization(request)
            decodedToken = jwt_decode(token)
            do_additional_token_verification(decodedToken)

        elif needs_additional_jwt_verification(request):
            token = get_http_authorization(info.context)
            decodedToken = jwt_decode(token)
            do_additional_token_verification(decodedToken)

        if not hasattr(request, "user"):
            request.user = AnonymousUser()

        return super().resolve(next, root, info, **kwargs)


def do_additional_token_verification(token):
    token_iat = datetime.fromtimestamp(token['origIat'], tz=timezone.utc)
    user = User.objects.get(email=token['email'])

    if user.last_jwt_iat > token_iat:
        raise JSONWebTokenError(INVALID_TOKEN)


def needs_additional_jwt_verification(request):
    is_anonymous = not hasattr(request, 'user') or request.user.is_anonymous
    return is_anonymous and get_http_authorization(request) is not None


def needs_live_client_jwt_verification(request):
    token = get_live_client_authorization(request)
    return token is not None


def get_live_client_authorization(request):
    auth = request.META.get('HTTP_AUTHORIZATION_LIVE_CLIENT', '').split()
    prefix = jwt_settings.JWT_AUTH_HEADER_PREFIX

    if len(auth) != 2 or auth[0].lower() != prefix.lower():
        return request.COOKIES.get(jwt_settings.JWT_COOKIE_NAME)
    return auth[1]


class OpentracingGrapheneMiddleware:
    @staticmethod
    def resolve(next_, root, info: ResolveInfo, **kwargs):
        if not should_trace(info):
            return next_(root, info, **kwargs)
        operation = f"{info.parent_type.name}.{info.field_name}"
        with opentracing.global_tracer().start_active_span(operation) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "graphql")
            span.set_tag("graphql.parent_type", info.parent_type.name)
            span.set_tag("graphql.field_name", info.field_name)
            return next_(root, info, **kwargs)


def get_app(auth_token) -> Optional[App]:
    qs = App.objects.filter(tokens__auth_token=auth_token, is_active=True)
    return qs.first()


def app_middleware(next, root, info, **kwargs):

    app_auth_header = "HTTP_AUTHORIZATION"
    prefix = "bearer"
    request = info.context

    if request.path == API_PATH:
        if not hasattr(request, "app"):
            request.app = None
            auth = request.META.get(app_auth_header, "").split()
            if len(auth) == 2:
                auth_prefix, auth_token = auth
                if auth_prefix.lower() == prefix:
                    request.app = SimpleLazyObject(lambda: get_app(auth_token))
    return next(root, info, **kwargs)


class ReadOnlyMiddleware:
    ALLOWED_MUTATIONS = [
        "checkoutAddPromoCode",
        "checkoutBillingAddressUpdate",
        "checkoutComplete",
        "checkoutCreate",
        "checkoutCustomerAttach",
        "checkoutCustomerDetach",
        "checkoutEmailUpdate",
        "checkoutLineDelete",
        "checkoutLinesAdd",
        "checkoutLinesUpdate",
        "checkoutRemovePromoCode",
        "checkoutPaymentCreate",
        "checkoutShippingAddressUpdate",
        "checkoutShippingMethodUpdate",
        "tokenCreate",
        "tokenVerify"
    ]

    @staticmethod
    def resolve(next_, root, info, **kwargs):
        operation = info.operation.operation
        if operation != "mutation":
            return next_(root, info, **kwargs)

        # Bypass users authenticated with ROOT_EMAIL
        request = info.context
        user = getattr(request, "user", None)
        if user and not user.is_anonymous:
            user_email = user.email
            root_email = getattr(settings, "ROOT_EMAIL", None)
            if root_email and user_email == root_email:
                return next_(root, info, **kwargs)

        for selection in info.operation.selection_set.selections:
            selection_name = str(selection.name.value)
            blocked = selection_name not in ReadOnlyMiddleware.ALLOWED_MUTATIONS
            if blocked:
                raise ReadOnlyException(
                    "Be aware admin pirate! API runs in read-only mode!"
                )
        return next_(root, info, **kwargs)


def process_view(self, request, view_func, *args):
    if hasattr(view_func, "view_class") and issubclass(
        view_func.view_class, GraphQLView
    ):
        request._graphql_view = True


if settings.ENABLE_DEBUG_TOOLBAR:
    import warnings

    try:
        from graphiql_debug_toolbar.middleware import DebugToolbarMiddleware
    except ImportError:
        warnings.warn("The graphiql debug toolbar was not installed.")
    else:
        DebugToolbarMiddleware.process_view = process_view
