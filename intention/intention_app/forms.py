from django import forms
from .models import Schedule

class scheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ('name', 'length', 'frequency', 'priority',)
