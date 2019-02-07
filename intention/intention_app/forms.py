from django import forms
from .models import Schedule

class scheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ('user_email', 'name', 'length', 'frequency', 'priority')
