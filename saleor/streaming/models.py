from django.db import models

from ..account.models import User
from ..order.models import Order


class TicketType:
    SINGLE = "single"
    TIMED = "timed"
    SEASON = "season"

    CHOICES = [
        (SINGLE, "single"),
        (TIMED, "timed"),
        (SEASON, "season"),
    ]


class ProductSlug:
    SINGLE = "single"
    CUP = "cup"
    SEASON = "season"
    PLAYOFF_SEASON = "playoff-season"
    REGULAR_SEASON = "regular-season"

    CHOICES = [
        (SINGLE, "single"),
        (CUP, "cup"),
        (SEASON, "season"),
        (PLAYOFF_SEASON, "playoff-season"),
        (REGULAR_SEASON, "regular-season"),
    ]


class StreamTicket(models.Model):
    type = models.CharField(
        max_length=256,
        blank=False,
        choices=[(type_name.upper(), type_name) for type_name, _ in TicketType.CHOICES],
    )
    user = models.ForeignKey(
        User,
        related_name="+",
        null=True,
        on_delete=models.SET_NULL
    )
    order = models.ForeignKey(
        Order,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL
    )
    access_code = models.CharField(max_length=256, blank=True, null=True)
    version = models.IntegerField(default=1)
    stream_type = models.CharField(max_length=256)
    game_id = models.CharField(max_length=256, blank=True, null=True)
    video_id = models.CharField(max_length=256, blank=True, null=True)
    season_id = models.CharField(max_length=256, blank=True, null=True)
    league_ids = models.CharField(max_length=2048, blank=True, null=True)
    team_ids = models.CharField(max_length=2048, blank=True, null=True)
    start_time = models.DateTimeField(default=None, editable=True, blank=True,
                                      null=True)
    expires = models.DateTimeField(default=None, editable=True, blank=True, null=True)
    hide_in_analytics = models.BooleanField(default=False, null=False)
    timed_type = models.CharField(max_length=256, default="none", null=False)
    for_guests = models.BooleanField(default=False, null=False)
    product_slug = models.CharField(
        max_length=256,
        choices=ProductSlug.CHOICES,
        null=True,
        default=None
    )

    class Meta:
        ordering = ("expires",)
