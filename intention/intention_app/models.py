from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from intention_app.scheduling.utils.datetime_utils import convert_to_military
from datetime import time

PERIOD_CHOICES = (('DAY', 'day'), ('WEEK', 'week'), ('MONTH', 'month'),)
TIMEUNIT_CHOICES = (('HOURS', 'hours'), ('MINUTES', 'minutes'),)
TIMERANGE_CHOICES = (('ANYTIME', 'anytime'), ('MORNING', 'morning'), ('AFTERNOON', 'afternoon'), ('EVENING', 'evening'))
WAKE_SLEEP_CHOICES = [(convert_to_military(h, m, ap), '%s:%s%s' % (h, m, ap)) for ap in ('am', 'pm')
                      for h in ([12] + list(range(1,12))) for m in ('00', '30')]


class Preferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    calendar_id = models.CharField(max_length=200, default='primary')
    day_start_time = models.TimeField(default=time(hour=8))
    day_end_time = models.TimeField(default=time(hour=0))

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    if created:
        Preferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    instance.preferences.save()


class Time(models.Model):
    wake_up_time = models.CharField(max_length=10, default = 8, choices = WAKE_SLEEP_CHOICES)
    sleep_time = models.CharField(max_length=10, default = 23, choices = WAKE_SLEEP_CHOICES)


class Schedule(models.Model):
    name = models.CharField(max_length=200, default = "task name")
    frequency = models.IntegerField(choices = [(x, x) for x in range(1, 8)], default = 1)
    period = models.CharField(max_length=200, choices = PERIOD_CHOICES, default="WEEK")
    duration = models.IntegerField(choices = [(x, x) for x in range(1, 61)], default = 1)
    timeunit = models.CharField(max_length=200, choices = TIMEUNIT_CHOICES, default="HOURS")
    timerange = models.CharField(max_length=200, choices = TIMERANGE_CHOICES, default="MORNING")
