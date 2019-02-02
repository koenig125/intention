from django.db import models
from django.conf import settings
from django.utils import timezone

FREQUNCY_CHOICES = (('day', 'DAY'), ('week', 'WEEK'), ('month', 'MONTH'),)
PRIORITY_CHOICES = (('high', 'HIGH'), ('middle', 'MIDDLE'), ('low', 'LOW'),)

class Schedule(models.Model):
    name = models.CharField(max_length=200)
    length = models.IntegerField(choices = [(x, x) for x in range(0, 50)], default = 1)
    frequency = models.CharField(max_length=200, choices = FREQUNCY_CHOICES)
    priority = models.CharField(max_length=200, choices = PRIORITY_CHOICES)
