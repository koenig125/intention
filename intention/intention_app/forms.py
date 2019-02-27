from django import forms
from .models import Schedule

from crispy_forms.helper import FormHelper
from crispy_forms import layout, bootstrap
from crispy_forms.bootstrap import InlineField, FormActions, StrictButton, Div
from crispy_forms.layout import Layout, HTML, MultiField
from crispy_forms import bootstrap, layout

class scheduleForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(scheduleForm, self).__init__(*args, **kwargs)
       
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.method = "POST"
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field.html'

        self.helper.layout = Layout(
        Div(
            HTML("<label> I want to</label>"),
            Div('name', css_class="col-sm-2"),
            HTML("<label> for </label> "),
            Div('duration', css_class="col-sm-2"),
            Div('timeunit', css_class="col-sm-2"),
            HTML("<label> a </label>"),
            Div('period', css_class="col-sm-2"),
            HTML("<label> I would like to do this (in the) </label>"),
            Div('timerange', css_class="col-sm-2"),
            HTML("<br>"),
            css_class='row',
        )
    )

        
    

    class Meta:
      model = Schedule
      fields = ('name', 'frequency', 'period', 'duration', 'timeunit', 'timerange', 'user_email')
    