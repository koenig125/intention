from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from intention_app.scheduling.rescheduler import get_events_current_day, reschedule
from intention_app.scheduling.scheduler import schedule
from intention_app.scheduling.utils.datetime_utils import convert_to_ampm
from intention_app.scheduling.utils.googleapi_utils import get_calendars
from .forms import *

CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
MONTHS = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June',
          '07': 'July', '08': 'August', '09':'September', '10': 'October', '11': 'November', '12': 'December'}


def homepage_view(request):
    """Application homepage. Links to login and introduces user to product."""
    context = {}
    return render(request, 'index.html', context=context)


@login_required
def scheduling_options_view(request):
    """Follows log-in - allows user to choose from available scheduling options"""
    template = loader.get_template('scheduling_options.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required
def user_preferences_view(request):
    """Follows log-in - allows user to enter scheduling preferences for account."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'user_preferences_view')
        return HttpResponseRedirect('authorize')
    template = loader.get_template('user_preferences.html')
    calendars = _get_calendar_list(request)
    all_cals_form = AllCalsForm(calendars=calendars)
    time_form = TimeForm()
    main_cal_form = MainCalForm(calendars=calendars)

    if request.method == "GET":
        context = {
            'message': 'tell us about yourself',
            'time_form': time_form,
            'main_cal_form': main_cal_form,
            'all_cals_form': all_cals_form, 
        }
        return HttpResponse(template.render(context, request))

    elif request.method == "POST":
        message = "Sorry, preferences could not be saved. Please try again!"
        print(request.POST)
        if 'sleep_time' in request.POST:
            time_form = TimeForm(request.POST)
            if time_form.is_valid():
                save_sleep_time(request)
                save_wake_time(request)
                message = "sleep and wake times saved!"
        elif 'calendar' in request.POST:
            save_calendar(request)
            message = "calendar choice saved!"
        context = {
            'message': message,
            'time_form': time_form,
            'main_cal_form': main_cal_form,
            'all_cals_form': all_cals_form,
        }
        return HttpResponse(template.render(context, request))


@login_required
def schedule_view(request):
    """Displays and submits scheduleForm - allows user to schedule events on their calendar."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'schedule_view')
        return HttpResponseRedirect('authorize')

    # User first arrives at scheduling page.
    if request.method == "GET":
        form = ScheduleForm()
        template = loader.get_template('schedule.html')
        context = {
            'message': 'make an intentional goal',
            'form': form,
        }
        return HttpResponse(template.render(context, request))

    # Scheduling form submitted - act on info.
    elif request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form_data = _unpack_form_data(request)
            preferences = User.objects.get(email=request.user.email).preferences
            credentials = Credentials(**request.session['credentials'])
            success = schedule(form_data, preferences, credentials)
            request.session['credentials'] = _credentials_to_dict(credentials)
            if not success:
                form = ScheduleForm()
                template = loader.get_template('schedule.html')
                context = {
                    'message': 'Looks like you\'re overbooked! Try again.',
                    'form': form,
                }
                return HttpResponse(template.render(context, request))
            else:
                template = loader.get_template('calendar.html')
                context =  {'event' : form_data, 'calendar_id': request.user.preferences.calendar_id}
                return HttpResponse(template.render(context, request))


@login_required
def reschedule_view(request):
    """Displays and reschedule interface - allows user to reschedule today's events."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'reschedule_view')
        return HttpResponseRedirect('authorize')

    # Populate list of rescheduling candidates with events.
    if request.method == "GET":
        preferences = User.objects.get(email=request.user.email).preferences
        ids_and_titles = _get_calendar_events(request, preferences)
        template = loader.get_template('reschedule.html')
        context =  {'events' : ids_and_titles, 'message': 'choose what you would like to reschedule'}
        return HttpResponse(template.render(context, request))

    # Rescheduling initiated after events selected by user.
    elif request.method == "POST":
        if request.POST.get('mydata') == '': # no events selected by user.
            return HttpResponseRedirect('reschedule')
        event_map = request.session['event_map']
        event_ids = request.POST.get('mydata').split(",")
        selected_events = [event_map[eid] for eid in event_ids]
        selected_events.sort(key=lambda x: x['start']['dateTime'])
        deadline = request.POST.get('schedule', '')
        preferences = User.objects.get(email=request.user.email).preferences
        credentials = Credentials(**request.session['credentials'])
        success = reschedule(selected_events, deadline, preferences, credentials)
        request.session['credentials'] = _credentials_to_dict(credentials)
        if not success:
            ids_and_titles = _get_calendar_events(request, preferences)
            template = loader.get_template('reschedule.html')
            context = {'events': ids_and_titles, 'message': 'Looks like you\'re overbooked! Try again.'}
            return HttpResponse(template.render(context, request))
        else:
            template = loader.get_template('calendar.html')
            template_events = [(event['summary'], convert_to_ampm(event['start']['dateTime'])) for event in selected_events]
            context = {'selected_events': template_events, 'calendar_id': request.user.preferences.calendar_id}
            return HttpResponse(template.render(context, request))


@login_required
def calendar_view(request):
    """Allows people to view their updated calendar schedule."""
    template = loader.get_template('calendar.html')
    context = {'calendar_id': request.user.preferences.calendar_id}
    return HttpResponse(template.render(context, request))


@login_required
def authorize(request):
    """Authorizes user's google account so that our code can edit their calendar."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = _build_full_view_url(request, 'oauth2callback')
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        approval_prompt='force',
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


def _build_full_view_url(request, view):
    """Returns the full url route to the view provided."""
    return 'http://' + request.environ['HTTP_HOST'] + reverse(view)


def _get_calendar_events(request, preferences):
    """Returns list of (event_id, event_name) tuples of calendar events for current day."""
    credentials = Credentials(**request.session['credentials'])
    ids_and_titles, event_map = get_events_current_day(credentials, preferences)
    request.session['credentials'] = _credentials_to_dict(credentials)
    request.session['event_map'] = event_map
    return ids_and_titles


def _get_calendar_list(request):
    """Returns list of (cal_id, cal_name) tuples of all user google calendars."""
    credentials = Credentials(**request.session['credentials'])
    calendar_list = get_calendars(credentials)
    request.session['credentials'] = _credentials_to_dict(credentials)
    return [(cal['id'], cal['summary']) for cal in calendar_list]


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
        'hours': request.POST['hours'],
        'minutes': request.POST['minutes'],
        'timerange': request.POST['timerange'],
        'startdate': request.POST['startdate']
    }


def save_wake_time(request):
    """Given request, saves user wake time preference to database."""
    wake_time = request.POST['wake_up_time']
    HH, MM = wake_time.split(':')
    wake_hour, wake_min = int(HH), int(MM)
    w_time = time(hour=wake_hour, minute=wake_min)
    user = User.objects.get(email=request.user.email)
    user.preferences.day_start_time = w_time
    user.save()


def save_sleep_time(request):
    """Given request, saves user sleep time preference to database."""
    sleep_time = request.POST['sleep_time']
    HH, MM = sleep_time.split(':')
    sleep_hour, sleep_min = int(HH), int(MM)
    s_time = time(hour=sleep_hour, minute=sleep_min)
    user = User.objects.get(email=request.user.email)
    user.preferences.day_end_time = s_time
    user.save()


def save_calendar(request):
    """Given request, saves user main calendar preference to databsse."""
    calendar_id = request.POST['calendar']
    user = User.objects.get(email=request.user.email)
    user.preferences.calendar_id = calendar_id
    user.save()
