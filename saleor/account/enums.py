from enum import Enum


class NewsletterStatus(Enum):
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    CLEANED = "cleaned"
    PENDING = "pending"
    TRANSACTIONAL = "transactional"
