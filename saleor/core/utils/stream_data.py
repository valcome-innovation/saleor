from ...account.models import User
from faker import Factory
from django.utils import timezone

from .random_data import create_address
from ...page.models import Page, PageType, PageTranslation
from ..utils import random_data
from ...tests.utils import dummy_editorjs

fake = Factory.create()


def create_gatling_test_user(how_many=100):
    for dummy in range(how_many):
        email = "gatling%d@valcome.tv" % dummy

        if not User.objects.filter(email=email).exists():
            user = create_user_object(email, "password")
            yield "User: %s" % (user.email,)


def create_user_object(email, password):
    address = create_address()
    user = User.objects.create_user(
        first_name=address.first_name,
        last_name=address.last_name,
        email=email,
        password=password,
        default_billing_address=address,
        default_shipping_address=address,
        is_active=True,
        note=fake.paragraph(),
        date_joined=fake.date_time(tzinfo=timezone.get_current_timezone()),
    )
    user.save()
    user.addresses.add(address)
    return user

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
    page_data = {
        "page_type_id": pk,
        "content": dummy_editorjs("This is an english page."),
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
