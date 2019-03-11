from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from .forms import scheduleForm
from intention_app.scheduling.scheduler import make_schedule
from intention_app.scheduling.rescheduler import get_events_current_day, reschedule
from django.contrib.auth.decorators import login_required
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']


def homepage_view(request):
    """Application homepage. Links to login and introduces user to product."""
    context = {}
    return render(request, 'index.html', context=context)


@login_required
def scheduling_options_view(request):
    """Follows log-in - allows user to choose from available scheduling options"""
    context = {}
    return render(request, 'scheduling_options.html', context=context)


@login_required
def schedule_view(request):
    if 'credentials' not in request.session:
        request.session['endurl'] = 'http://127.0.0.1:8000/schedule'
        return HttpResponseRedirect('authorize')
    template = loader.get_template('schedule.html')

    # Scheduling form submitted - act on info.
    if request.method == "POST":
        form = scheduleForm(request.POST)
        if form.is_valid():
            form_data = unpack_form_data(request)
            credentials = Credentials(**request.session['credentials'])
            success = make_schedule(form_data, credentials)
            request.session['credentials'] = credentials_to_dict(credentials)
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


@login_required
def reschedule_view(request):
    if 'credentials' not in request.session:
        request.session['endurl'] = 'http://127.0.0.1:8000/reschedule'
        return HttpResponseRedirect('authorize')
    template = loader.get_template('reschedule.html')
    tasks = ['do laundry', 'clean room', 'call mom', 'prep dinner', 'email Professor Joe']

    # Populate list of rescheduling candidates with events.
    if request.method == "GET":
        credentials = Credentials(**request.session['credentials'])
        tasks, all_events = get_events_current_day(credentials)
        request.session['credentials'] = credentials_to_dict(credentials)
        request.session['events'] = all_events
        context =  {'tasks' : tasks, 'message': 'Select Events to Reschedule'}
        return HttpResponse(template.render(context, request))

    # Called when rescheduling initiated after events selected.
    elif request.method == "POST":
        if request.POST.get('mydata') == '': # no events selected by user.
            return HttpResponseRedirect('reschedule')
        events = request.session['events']
        event_ids = request.POST.get('mydata').split(",")
        selected_events = [events[eid] for eid in event_ids]
        deadline = request.POST.get('schedule', '')
        credentials = Credentials(**request.session['credentials'])
        if not reschedule(selected_events, deadline, credentials):
            tasks, all_events = get_events_current_day(credentials)
            request.session['credentials'] = credentials_to_dict(credentials)
            request.session['events'] = all_events
            context = {'tasks': tasks, 'message': 'Looks like you\'re overbooked! Try again.'}
            return HttpResponse(template.render(context, request))
        request.session['credentials'] = credentials_to_dict(credentials)
        return HttpResponseRedirect('calendar')


@login_required
def calendar_view(request):
    """Allows people to view their updated calendar schedule."""
    context = {}
    return render(request, 'calendar.html', context=context)


@login_required
def authorize(request):
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = 'http://127.0.0.1:8000/oauth2callback'
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
    )
    request.session['state'] = state
    return HttpResponseRedirect(authorization_url)


@login_required
def oauth2callback(request):
    state = request.session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = 'http://127.0.0.1:8000/oauth2callback'
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    return HttpResponseRedirect(request.session['endurl'])


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def unpack_form_data(request):
    form_data = {}
    form_data['name'] = request.POST['name']
    form_data['frequency'] = request.POST['frequency']
    form_data['period'] = request.POST['period']
    form_data['duration'] = request.POST['duration']
    form_data['timeunit'] = request.POST['timeunit']
    form_data['timerange'] = request.POST['timerange']
    return form_data
