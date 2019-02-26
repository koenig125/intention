from django.db import models

PERIOD_CHOICES = (('DAY', 'daily'), ('WEEK', 'weekly'), ('MONTH', 'monthly'),)
TIMEUNIT_CHOICES = (('HOURS', 'hours'), ('MINUTES', 'minutes'),)
TIMERANGE_CHOICES = (('ANYTIME', 'anytime'), ('MORNING', 'morning'), ('AFTERNOON', 'afternoon'), ('EVENING', 'evening'))


class Schedule(models.Model):
    name = models.CharField(max_length=200)
    frequency = models.IntegerField(choices = [(x, x) for x in range(1, 8)], default = 1)
    period = models.CharField(max_length=200, choices = PERIOD_CHOICES, default="WEEK")
    duration = models.IntegerField(choices = [(x, x) for x in range(1, 61)], default = 1)
    timeunit = models.CharField(max_length=200, choices = TIMEUNIT_CHOICES, default="HOURS")
    timerange = models.CharField(max_length=200, choices = TIMERANGE_CHOICES, default="ANYTIME")
    user_email = models.CharField(max_length=200, null=True)