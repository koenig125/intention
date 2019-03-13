from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from .forms import scheduleForm
from intention_app.scheduling.scheduler import make_schedule
from intention_app.scheduling.rescheduler import get_events_current_day, reschedule
from django.contrib.auth.decorators import login_required
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from intention_app.scheduling.utils.datetime_utils import parse_datetime
from datetime import datetime


CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
MONTHS = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09':'September', '10': 'October', '11': 'November', '12': 'December'}


def homepage_view(request):
    """Application homepage. Links to login and introduces user to product."""
    context = {}
    return render(request, 'index.html', context=context)


@login_required
def scheduling_options_view(request):
    """Follows log-in - allows user to choose from available scheduling options."""
    context = {}
    return render(request, 'scheduling_options.html', context=context)


@login_required
def schedule_view(request):
    """Displays and submits scheduleForm - allows user to schedule events on their calendar."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'schedule_view')
        return HttpResponseRedirect('authorize')
    template = loader.get_template('schedule.html')

    # User first arrives at scheduling page.
    if request.method == "GET":
        form = scheduleForm()
        context = {
            'message': 'Make An Intentional Goal.',
            'form': form,
        }
        return HttpResponse(template.render(context, request))

    # Scheduling form submitted - act on info.
    elif request.method == "POST":
        form = scheduleForm(request.POST)
        if form.is_valid():
            form_data = _unpack_form_data(request)
            credentials = Credentials(**request.session['credentials'])
            success = make_schedule(form_data, credentials)
            request.session['credentials'] = _credentials_to_dict(credentials)
            if not success:
                form = scheduleForm()
                context = {
                    'message': 'Looks like you\'re overbooked! Try again.',
                    'form': form,
                }
                return HttpResponse(template.render(context, request))
            else:
                template = loader.get_template('calendar.html')
                context =  {'event' : form_data }
                print(form_data)
                return HttpResponse(template.render(context, request))
                # return HttpResponseRedirect('calendar')


@login_required
def reschedule_view(request):
    """Displays and reschedule interface - allows user to reschedule today's events."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'reschedule_view')
        return HttpResponseRedirect('authorize')
    template = loader.get_template('reschedule.html')

    # Populate list of rescheduling candidates with events.
    if request.method == "GET":
        ids_and_titles = _get_rescheduling_info(request)
        context =  {'events' : ids_and_titles, 'message': 'Select Events to Reschedule'}
        return HttpResponse(template.render(context, request))

    # Rescheduling initiated after events selected by user.
    elif request.method == "POST":
        if request.POST.get('mydata') == '': # no events selected by user.
            return HttpResponseRedirect('reschedule')
        event_map = request.session['event_map']
        event_ids = request.POST.get('mydata').split(",")
        selected_events = [event_map[eid] for eid in event_ids]
        deadline = request.POST.get('schedule', '')
        credentials = Credentials(**request.session['credentials'])
        if not reschedule(selected_events, deadline, credentials):
            # Reschedule attempt failed - inform user.
            ids_and_titles = _get_rescheduling_info(request)
            context = {'events': ids_and_titles, 'message': 'Looks like you\'re overbooked! Try again.'}
            return HttpResponse(template.render(context, request))
        request.session['credentials'] = _credentials_to_dict(credentials)
        template = loader.get_template('calendar.html')
        template_events = [(event['summary'], dateTime_helper(event['start']['dateTime'])) for event in selected_events]
        context = {'selected_events': template_events, 'user_email': request.user.email}
        return HttpResponse(template.render(context, request))


@login_required
def calendar_view(request):
    """Allows people to view their updated calendar schedule."""
    template = loader.get_template('calendar.html')
    context = {'user_email': request.user.email}
    return HttpResponse(template.render(context, request))


@login_required
def authorize(request):
    """Authorizes user's google account so that our code can edit their calendar."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = _build_full_view_url(request, 'oauth2callback')
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
    )
    request.session['state'] = state
    return HttpResponseRedirect(authorization_url)


@login_required
def oauth2callback(request):
    """Authorization callback code, called during oauth callback."""
    state = request.session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = _build_full_view_url(request, 'oauth2callback')
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    request.session['credentials'] = _credentials_to_dict(credentials)
    return HttpResponseRedirect(request.session['endurl'])


def _credentials_to_dict(credentials):
    """Helper function that adds sign-in credentials to dictionary."""
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def _unpack_form_data(request):
    """Helper method that unpacks the data from scheduleForm."""
    return {
        'name': request.POST['name'],
        'frequency': request.POST['frequency'],
        'period': request.POST['period'],
        'duration': request.POST['duration'],
        'timeunit': request.POST['timeunit'],
        'timerange': request.POST['timerange']
    }

def dateTime_helper(datestr):
  dateobj = parse_datetime(datestr)
  am_pm = 'am'
  month = dateobj.date().month
  day = dateobj.date().day
  hour = dateobj.time().hour
  min = dateobj.time().min
  if hour > 12:
      am_pm = 'pm'
      hour = hour - 12
  return str(month) + '/' + str(day) + ' at ' +  str(hour) + ':' + str(min)[0:2] + ' ' + am_pm

def _get_rescheduling_info(request):
    """Helper method that retrieves the rescheduling data from the session."""
    credentials = Credentials(**request.session['credentials'])
    ids_and_titles, event_map = get_events_current_day(credentials)
    request.session['credentials'] = _credentials_to_dict(credentials)
    request.session['event_map'] = event_map
    return ids_and_titles


def _build_full_view_url(request, view):
    return 'http://' + request.environ['HTTP_HOST'] + reverse(view)
