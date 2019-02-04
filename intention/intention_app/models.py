from django.db import models
from django.conf import settings
from django.utils import timezone

FREQUNCY_CHOICES = (('DAY', 'day'), ('WEEK', 'week'), ('MONTH', 'month'),)
PRIORITY_CHOICES = (('HIGH', 'high'), ('MIDDLE', 'middle'), ('LOW', 'low'),)

class Schedule(models.Model):
    name = models.CharField(max_length=200)
    length = models.IntegerField(choices = [(x, x) for x in range(0, 50)], default = 1)
    frequency = models.CharField(max_length=200, choices = FREQUNCY_CHOICES)
    priority = models.CharField(max_length=200, choices = PRIORITY_CHOICES)
