from typing import Optional

from ....models import Payment
from ..... import settings
from .....streaming import stream_settings


# Verify if stripe request comes from same app (skipped for local development)
def has_matching_app_id(payment_intent):
    return not hasattr(payment_intent.metadata, "app_id") \
           or payment_intent.metadata.app_id == stream_settings.APP_ID \
           or settings.DEBUG


def is_sofort_payment(payment_intent):
    return hasattr(payment_intent, "payment_method_types") \
            and "sofort" in payment_intent.payment_method_types


def get_payment_object(event):
    return event.data.object


def get_payment(payment_intent_id: str) -> Optional[Payment]:
    return (
        Payment.objects
        .prefetch_related("checkout")
        .select_for_update(of=("self",))
        .filter(transactions__token=payment_intent_id)
        .first()
    )
