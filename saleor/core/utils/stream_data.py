from ...page.models import Page
from random_data import create_fake_user


def create_users(how_many=10):
    for dummy in range(how_many):
        user = create_fake_user()
        yield "User: %s" % (user.email,)


def create_page(title, slug):
    content = """
    <h2>E-commerce for the PWA era</h2>
    <h3>A modular, high performance e-commerce storefront built with GraphQL,
        Django, and ReactJS.</h3>
    <p>Saleor is a rapidly-growing open source e-commerce platform that has served
       high-volume companies from branches like publishing and apparel since 2012.
       Based on Python and Django, the latest major update introduces a modular
       front end with a GraphQL API and storefront and dashboard written in React
       to make Saleor a full-functionality open source e-commerce.</p>
    <p><a href="https://github.com/mirumee/saleor">Get Saleor today!</a></p>
    """
    content_json = {
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
        "content": content,
        "content_json": content_json,
        "title": title,
        "is_published": True,
    }
    page, dummy = Page.objects.get_or_create(slug=slug, defaults=page_data)
    yield "Page %s created" % page.slug
