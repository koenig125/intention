from django.http import HttpResponse, HttpResponseRedirect
<<<<<<< HEAD
from django.template import RequestContext, loader
=======
from django.template import loader
from django.shortcuts import render
>>>>>>> 4a43fbb507a01e68453743cc02904850b8043eea
from .forms import scheduleForm
from intention_app.scheduling.scheduler import make_schedule

# Renders the Intention App homepage
def schedule_view(request):
    template = loader.get_template('schedule.html')
    form = scheduleForm()
    if request.method == "POST": # trying to submit form
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
                print("loading calendar after form submit")
                return HttpResponseRedirect('calendar')
    else:
       context = {
         'form' :form,
         'message': 'What do you want to accomplish?',
      }
    return HttpResponse(template.render(context, request))

def reschedule_view(request):
    template = loader.get_template('reschedule.html')
    print("in reschedule view")
    print(request)
    tasks = ['do laundry', 'clean room', 'call mom', 'prep dinner', 'email Professor Joe']
    if request.method == "GET": #trying to choose tasks to reschedule
        print("in get")
        context =  {'tasks' : tasks,}     
    elif request.method == "POST":
        # this will be called when someone wants to reschedule something
        print ("in post")
        schedule = request.POST.get('schedule', '')
        tasks_returned = request.POST.get('mydata').split(",")
        print ("TASKS: ", tasks_returned)
        print ("SCHEDULE: ", schedule)
        # will call reschedule from scheduler.py
        #will render the calendar view
        return HttpResponseRedirect('calendar')

        context =  {'tasks' : tasks,}   
    
    return HttpResponse(template.render(context, request))
   

# A view that will allow people to choose if they want to schedule or reschedule a goal.
def homepage_view(request):
    context = {}
    return render(request, 'index.html', context=context)

# A view that will allow people to view their updated calendar schedule.
def calendar_view(request):
    context = {}
    return render(request, 'calendar.html', context=context)
    
# A view following log-in/authentication that will allow user to choose from available scheduling options
def scheduling_options_view(request):
    context = {}
    return render(request, 'scheduling_options.html', context=context)
