from django.db import models

PERIOD_CHOICES = (('DAY', 'day'), ('WEEK', 'week'), ('MONTH', 'month'),)
TIMEUNIT_CHOICES = (('HOURS', 'hours'), ('MINUTES', 'minutes'),)
PRIORITY_CHOICES = (('HIGH', 'high'), ('MIDDLE', 'middle'), ('LOW', 'low'),)


class Schedule(models.Model):
    name = models.CharField(max_length=200)
    frequency = models.IntegerField(choices = [(x, x) for x in range(1, 8)], default = 1)
    period = models.CharField(max_length=200, choices = PERIOD_CHOICES, default="WEEK")
    duration = models.IntegerField(choices = [(x, x) for x in range(1, 61)], default = 1)
    timeunit = models.CharField(max_length=200, choices = TIMEUNIT_CHOICES, default="HOURS")
    priority = models.CharField(max_length=200, choices = PRIORITY_CHOICES)
    user_email = models.CharField(max_length=200, null=True)