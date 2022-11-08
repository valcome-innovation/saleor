from enum import Enum

import jwt


# VACLOME
class TokenDeactivatedError(jwt.InvalidTokenError):
    """
    Raised when a token already deactivated token gets used.
    A token gets deactivated if another user logs in with the same account.
    """
    pass


class ShopErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    CANNOT_FETCH_TAX_RATES = "cannot_fetch_tax_rates"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"


class MetadataErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"


class TranslationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"


class UploadErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
