from ...page.models import Page, PageType
from ..utils import random_data


def create_users(how_many=10):
    for dummy in range(how_many):
        user = random_data.create_fake_user()
        yield "User: %s" % (user.email,)


def create_page_type(pk, title, slug):
    data = {
        "pk": pk,
        "fields": {
            "private_metadata": {},
            "metadata": {},
            "name": title,
            "slug": slug,
        },
    }

    page_type, _ = PageType.objects.update_or_create(
        pk=pk, **data["fields"]
    )
    yield "Page type %s created" % page_type.slug


def create_page(pk, title, slug):
    content = {
        "blocks": [
            {
                "key": "",
                "data": {},
                "text": "E-commerce for the PWA era",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "A modular, high performance e-commerce storefront "
                "built with GraphQL, Django, and ReactJS.",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "Saleor is a rapidly-growing open source e-commerce platform "
                "that has served high-volume companies from branches like "
                "publishing and apparel since 2012. Based on Python and "
                "Django, the latest major update introduces a modular "
                "front end with a GraphQL API and storefront and dashboard "
                "written in React to make Saleor a full-functionality "
                "open source e-commerce.",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "Get Saleor today!",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [{"key": 0, "length": 17, "offset": 0}],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {
            "0": {
                "data": {"url": "https://github.com/mirumee/saleor"},
                "type": "LINK",
                "mutability": "MUTABLE",
            }
        },
    }
    page_data = {
        "page_type_id": pk,
        "content": content,
        "title": title,
        "is_published": True,
    }
    page, dummy = Page.objects.get_or_create(slug=slug, defaults=page_data)
    yield "Page %s created" % page.slug
