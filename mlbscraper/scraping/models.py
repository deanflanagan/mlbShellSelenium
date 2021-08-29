from django.db import models
# from django.utils import
# Create your models here.


class Game(models.Model):
    sport = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    league = models.CharField(max_length=30)
    tournament_id = models.IntegerField()
    match_id = models.CharField(max_length=8)
    match_utc_time = models.DateTimeField()
    match_status = models.CharField(max_length=3)
    team = models.CharField(max_length=30)
    opposition = models.CharField(max_length=30)
    ft1 = models.IntegerField(null=True)
    ft2 = models.IntegerField(null=True)
    # home = models.CharField(max_length=30)
    # away = models.CharField(max_length=30)
    home_odds = models.DecimalField(max_digits=6, decimal_places=3)
    away_odds = models.DecimalField(max_digits=6, decimal_places=3)
    draw_odds = models.DecimalField(
        max_digits=6, decimal_places=3, blank=True, null=True)

    class Meta:
        ordering = ['match_utc_time']

    class Admin:
        pass
