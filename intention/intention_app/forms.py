from django import forms
from .models import *

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import Div
from crispy_forms.layout import Layout, HTML


class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ('time',)


class MainCalForm(forms.Form):

    def __init__(self, *args, **kwargs):
        cals = kwargs.pop('calendars')
        super(MainCalForm, self).__init__(*args, **kwargs)
        self.fields['calendar'] = forms.ChoiceField(choices=cals)


    class Meta:
        fields = ('calendar',)


class ScheduleForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
       
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.method = "POST"
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field.html'

        self.helper.layout = Layout(
        Div(
            HTML("<label> i want to </label>"),
            Div('name', css_class="col-xs-6"),
            Div('frequency', css_class="col-sm-2"),
            HTML("<label class=\"form_label\"> times a </label>"),
            Div('period', css_class="col-sm-2"),
            HTML("<label class=\"form_punctuation\"> for </label>"),
            Div('duration', css_class="col-xs-6"),
            Div('timeunit', css_class="col-xs-6"),
            HTML("<label class=\"form_label\">.</label>"),
            css_class='row',
        ),

         Div(
            HTML("<label> i prefer to do this in the  </label>"),
            Div('timerange', css_class="col-sm-2"),
            HTML("<label class=\"form_punctuation\">.</label>"),
            css_class='row',
        )
    )

    class Meta:
      model = Schedule
      fields = ('name', 'frequency', 'period', 'duration', 'timeunit', 'timerange')
