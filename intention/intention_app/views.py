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
            name = request.POST['name']
            length = request.POST['length']
            frequency = request.POST['frequency']
            priority = request.POST['priority']
            return HttpResponseRedirect('schedule')
    else:
        form = scheduleForm()
        context = {
          'message': 'Let\'s get productive!',
          'form': form,
          'user_id': 'reymbarcelo'
        }
    return HttpResponse(template.render(context, request))

# A view that will allow people to view their updated calendar schedule.
def schedule_view(request):
    template = loader.get_template('schedule.html')
    context = {
        'message': 'Here is your new calendar!',
        'user_email': user_email
    }
    return HttpResponse(template.render(context, request))