from django import forms
from .models import Schedule

class scheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ('name', 'frequency', 'period', 'duration', 'timeunit', 'timerange', 'user_email')