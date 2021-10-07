import logging

from django.core.cache import cache
from django.db.models import QuerySet
from graphql import ResolveInfo
import json

from ..settings import CACHES

logger = logging.getLogger(__name__)


class CachePrefix:
    CATEGORY = 'Category'
    CATEGORY_PATTERN = f"{CATEGORY}:*"
    PAGE = 'Page'
    PAGE_PATTERN = f"{PAGE}:*"
    PRODUCT = 'Product'
    PRODUCT_PATTERN = f"{PRODUCT}:*"
    ADDRESS = 'Address'
    ADDRESS_PATTERN = f"{ADDRESS}:*"


def cache_query(qs: "QuerySet", action):
    cached_value = cache.get(qs.query)

    if cached_value:
        return cached_value
    else:
        return action()


def invalidate_cache(pattern: "str"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_redis_cache():
                nr_deleted = cache.delete_pattern(pattern)
                # logger.debug(f"Deleted {nr_deleted} cache entries")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cached_resolver(prefix: "str", with_user: "bool" = False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_redis_cache():
                return func(*args, **kwargs)

            info = next(arg for arg in args if isinstance(arg, ResolveInfo))
            user = info.context.user
            operation = f"{info.parent_type.name}:{info.field_name}"

            if type(kwargs) != 'str':
                variables = json.dumps(kwargs).replace(' ', '')
            else:
                variables = kwargs

            if with_user and user is not None and user.id is not None:
                key = f"{prefix}:{operation}:{user.id}:{variables}"
            else:
                key = f"{prefix}:{operation}:{variables}"

            cached_value = cache.get(key)

            if cached_value:
                # logger.debug(f"Using cache: {key}")
                return cached_value
            else:
                # logger.debug(f"Key: {key}")
                value = func(*args, **kwargs)
                cache.set(key, value)
                return value
        return wrapper
    return decorator


def is_redis_cache():
    return "RedisCache" in CACHES["default"]["BACKEND"]
