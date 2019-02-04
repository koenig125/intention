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
            print("POST IS VALID")
            # form.save()
            # need to set up database table in order to save the form in line above
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
    }
    return HttpResponse(template.render(context, request))