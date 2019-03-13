from django.db import models
from intention_app.scheduling.utils.datetime_utils import convert_to_military

PERIOD_CHOICES = (('DAY', 'day'), ('WEEK', 'week'), ('MONTH', 'month'),)
TIMEUNIT_CHOICES = (('HOURS', 'hours'), ('MINUTES', 'minutes'),)
TIMERANGE_CHOICES = (('ANYTIME', 'anytime'), ('MORNING', 'morning'), ('AFTERNOON', 'afternoon'), ('EVENING', 'evening'))
WAKE_SLEEP_CHOICES = [(convert_to_military(h, m, ap), '%s:%s%s' % (h, m, ap)) for ap in ('am', 'pm')
                      for h in ([12] + list(range(1,12))) for m in ('00', '30')]


class Time(models.Model):
    time = models.CharField(max_length=10, choices = WAKE_SLEEP_CHOICES)


class Schedule(models.Model):
    name = models.CharField(max_length=200)
    frequency = models.IntegerField(choices = [(x, x) for x in range(1, 8)], default = 1)
    period = models.CharField(max_length=200, choices = PERIOD_CHOICES, default="WEEK")
    duration = models.IntegerField(choices = [(x, x) for x in range(1, 61)], default = 1)
    timeunit = models.CharField(max_length=200, choices = TIMEUNIT_CHOICES, default="HOURS")
    timerange = models.CharField(max_length=200, choices = TIMERANGE_CHOICES, default="MORNING")
