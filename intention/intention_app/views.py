from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from .forms import scheduleForm

# Renders the Intention App homepage
def homepage_view(request):
    template = loader.get_template('index.html')
    context = {}
    if request.method == "POST":
        form = scheduleForm(request.POST)
        print(form.errors)
        if form.is_valid():
            form_data = {}
            form_data['user_email'] = request.POST['user_email']
            form_data['name'] = request.POST['name']
            form_data['length'] = request.POST['length']
            form_data['frequency'] = request.POST['frequency']
            form_data['priority'] = request.POST['priority']
            # TODO: pass form_data to the schedule_view function
            return HttpResponseRedirect('schedule')
    else:
        form = scheduleForm()
        context = {
          'message': 'Let\'s get productive!',
          'form': form,
        }
    return HttpResponse(template.render(context, request))

# A view that will allow people to view their updated calendar schedule.
def schedule_view(request):
    template = loader.get_template('schedule.html')
    context = {
        'message': 'Here is your new calendar!',
        'user_email': ''
    }
    return HttpResponse(template.render(context, request))