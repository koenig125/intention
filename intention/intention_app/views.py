from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from .forms import scheduleForm
from .scheduler import make_schedule

# Renders the Intention App homepage
def schedule_or_reschedule_view(request):
    template = loader.get_template('schedule_or_reschedule.html')
    form = scheduleForm()
    if request.method == "POST":
        form = scheduleForm(request.POST)
        if form.is_valid():
            form_data = {}
            form_data['name'] = request.POST['name']
            form_data['frequency'] = request.POST['frequency']
            form_data['period'] = request.POST['period']
            form_data['duration'] = request.POST['duration']
            form_data['timeunit'] = request.POST['timeunit']
            form_data['timerange'] = request.POST['timerange']
            success = make_schedule(form_data)
            if not success: # Couldn't schedule user's request.
                form = scheduleForm()
                context = {
                    'message': 'Sorry, you\'re overbooked! Try again.',
                    'form': form,
                }
                return HttpResponse(template.render(context, request))
            else:
                return HttpResponseRedirect('calendar')
    else:
       context = {
         'form' :form,
         'message': 'What do you want to accomplish?',
      }
    return HttpResponse(template.render(context, request))

# A view that will allow people to choose if they want to schedule or reschedule a goal.
def homepage_view(request):
    template = loader.get_template('index.html')
    context = {}
    return render(request, 'index.html', context=context)

# A view that will allow people to view their updated calendar schedule.
def calendar_view(request):
    template = loader.get_template('calendar.html')
    context = {}
    return render(request, 'calendar.html', context=context)
    # A view that will allow people to view their updated calendar schedule.
