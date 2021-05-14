from django.db import models

from saleor.account.models import User


class TicketType:
    SINGLE = "single"
    DAY = "day"
    TEAM = "team"
    LEAGUE = "league"

    CHOICES = [
        (SINGLE, 'single'),
        (DAY, 'day'),
        (TEAM, 'team'),
        (LEAGUE, 'league')
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
    version = models.IntegerField(default=1)
    game_id = models.CharField(max_length=256, blank=True, null=True)
    team_id = models.CharField(max_length=256, blank=True, null=True)
    season_id = models.CharField(max_length=256, blank=True, null=True)
    expires = models.DateTimeField(default=None, editable=True, blank=True, null=True)

    class Meta:
        ordering = ("expires",)
