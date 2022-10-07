from ...account.models import User
from faker import Factory
from django.utils import timezone

from .random_data import create_address
from ...page.models import Page, PageType, PageTranslation
from ..utils import random_data
from ...tests.utils import dummy_editorjs

fake = Factory.create()


def create_test_user(how_many=100):
    for dummy in range(how_many):
        address = create_address()

        if not User.objects.filter(email="gatling%d@valcome.tv" % dummy).exists():
            user = User.objects.create_user(
                first_name=address.first_name,
                last_name=address.last_name,
                email="gatling%d@valcome.tv" % dummy,
                password="password",
                default_billing_address=address,
                default_shipping_address=address,
                is_active=True,
                note=fake.paragraph(),
                date_joined=fake.date_time(tzinfo=timezone.get_current_timezone()),
            )
            user.save()
            user.addresses.add(address)
            yield "User: %s" % (user.email,)


def create_users(how_many=10):
    for dummy in range(how_many):
        user = random_data.create_fake_user("password")
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

    return page


def create_page_translation(page):
    page_translation, dummy = PageTranslation.objects.get_or_create(
        language_code="de",
        page=page,
        title="Der Titel ist deutsch",
        content=dummy_editorjs("Diese Seite ist deutsch."),
    )

    yield "Page %s translated" % page.slug
