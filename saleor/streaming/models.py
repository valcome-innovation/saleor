from django.db import models

from saleor.account.models import User


class TicketType:
    SINGLE = "single"
    TIMED = "timed"
    SEASON = "season"

    CHOICES = [
        (SINGLE, 'single'),
        (TIMED, 'timed'),
        (SEASON, 'season'),
    ]


class StreamTicket(models.Model):
    type = models.CharField(max_length=256, blank=False, choices=[
        (type_name.upper(), type_name) for type_name, _ in TicketType.CHOICES
    ],)
    user = models.ForeignKey(
        User,
        related_name="+",
        null=True,
        on_delete=models.SET_NULL
    )
    access_code = models.CharField(max_length=256, blank=True, null=True)
    version = models.IntegerField(default=1)
    game_id = models.CharField(max_length=256, blank=True, null=True)
    season_id = models.CharField(max_length=256, blank=True, null=True)
    start_time = models.DateTimeField(default=None, editable=True, blank=True, null=True)
    expires = models.DateTimeField(default=None, editable=True, blank=True, null=True)
    league_ids = models.CharField(max_length=256, blank=True, null=True)
    team_ids = models.CharField(max_length=256, blank=True, null=True)
    is_free = models.BooleanField(default=False, null=False)
    timed_type = models.CharField(max_length=256, default="none", null=False)

    class Meta:
        ordering = ("expires",)
