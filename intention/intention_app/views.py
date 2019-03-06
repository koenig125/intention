from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from .forms import scheduleForm
from intention_app.scheduling.scheduler import make_schedule
from intention_app.scheduling.rescheduler import get_events_current_day


def homepage_view(request):
    """Application homepage. Links to login and introduces user to product."""
    context = {}
    return render(request, 'index.html', context=context)


def scheduling_options_view(request):
    """Follows log-in - allows user to choose from available scheduling options"""
    context = {}
    return render(request, 'scheduling_options.html', context=context)


def schedule_view(request):
    template = loader.get_template('schedule.html')

    # Scheduling form submitted - act on info.
    if request.method == "POST":
        form = scheduleForm(request.POST)
        if form.is_valid():
            form_data = unpack_form_data(request)
            success = make_schedule(form_data)
            if not success:
                form = scheduleForm()
                context = {
                    'message': 'Sorry, you\'re overbooked! Try again.',
                    'form': form,
                }
                return HttpResponse(template.render(context, request))
            else:
                return HttpResponseRedirect('calendar')

    # User first arrives at scheduling page.
    else:
        form = scheduleForm()
        context = {
            'form' :form,
            'message': 'What do you want to accomplish?',
        }
        return HttpResponse(template.render(context, request))


def reschedule_view(request):
    template = loader.get_template('reschedule.html')
    tasks = ['do laundry', 'clean room', 'call mom', 'prep dinner', 'email Professor Joe']

    # Populate list of rescheduling candidates with events.
    if request.method == "GET":
        tasks = get_events_current_day()
        ids = [task[0] for task in tasks]
        titles = [task[1] for task in tasks]
        context =  {'tasks' : titles,}
        return HttpResponse(template.render(context, request))

    # Called when rescheduling initiated after events selected.
    elif request.method == "POST":
        print ("in post")
        schedule = request.POST.get('schedule', '')
        tasks_returned = request.POST.get('mydata').split(",")
        print ("TASKS: ", tasks_returned)
        print ("SCHEDULE: ", schedule)
        # will call reschedule from scheduler.py
        # will render the calendar view
        context =  {'tasks' : tasks,} 
        return HttpResponseRedirect('calendar')


def calendar_view(request):
    """Allows people to view their updated calendar schedule."""
    context = {}
    return render(request, 'calendar.html', context=context)


def unpack_form_data(request):
    form_data = {}
    form_data['name'] = request.POST['name']
    form_data['frequency'] = request.POST['frequency']
    form_data['period'] = request.POST['period']
    form_data['duration'] = request.POST['duration']
    form_data['timeunit'] = request.POST['timeunit']
    form_data['timerange'] = request.POST['timerange']
    return form_data
