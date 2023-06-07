from stripe.api_resources.event import Event
from stripe.stripe_object import StripeObject


class StripeEventRequest:
    id: str
    idempotency_key: str


class StripeEventData:
    object: StripeObject


class StripeEvent(Event):
    id: str
    type: str
    created: int
    object: str
    livemode: bool
    api_version: str
    pending_webhooks: int
    data: StripeEventData
    request: dict
