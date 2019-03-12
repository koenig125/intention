from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from .forms import scheduleForm, timeForm
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
def user_preferences_view(request):
    """Follows log-in - allows user to enter scheduling preferences for account."""
    if 'credentials' not in request.session:
        request.session['endurl'] = _build_full_view_url(request, 'user_preferences_view')
        return HttpResponseRedirect('authorize')

    if request.method == "GET":
        template = loader.get_template('user_preferences.html')
        wake_form = timeForm()
        sleep_form = timeForm()
        context = {
            'sleep_form': sleep_form,
            'wake_form': wake_form,
            'message': 'Enter Your Preferences'
        }
        return HttpResponse(template.render(context, request))

    if request.method == "POST":

        # User udpated sleep time
        if 'sleep' in request.POST:
            sleep_form = timeForm(request.POST)
            if sleep_form.is_valid():
                sleep_time = request.POST['time']
                # save to user record in db
            else:
                pass
                # invalid form response

        # User updated wake time.
        elif 'wake' in request.POST:
            wake_form = timeForm(request.POST)
            if wake_form.is_valid():
                wake_time = request.POST['time']
                # save to user record in db
            else:
                pass
                # invalid form response

        # User updated main calendar.
        elif 'main_cal' in request.POST:
            pass

        # User updated all calendars.
        elif 'all_cals' in request.POST:
            pass

        template = loader.get_template('user_preferences.html')
        wake_form = timeForm()
        sleep_form = timeForm()
        context = {
            'sleep_form': sleep_form,
            'wake_form': wake_form,
            'message': 'Your Preferences Have Been Saved!'
        }
        return HttpResponse(template.render(context, request))


@login_required
def scheduling_options_view(request):
    """Follows log-in - allows user to choose from available scheduling options"""
    template = loader.get_template('scheduling_options.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required
def schedule_view(request):
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
                return HttpResponseRedirect('calendar')


@login_required
def reschedule_view(request):
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
            request.session['credentials'] = _credentials_to_dict(credentials)
            ids_and_titles = _get_rescheduling_info(request)
            context = {'events': ids_and_titles, 'message': 'Looks like you\'re overbooked! Try again.'}
            return HttpResponse(template.render(context, request))
        request.session['credentials'] = _credentials_to_dict(credentials)
        return HttpResponseRedirect('calendar')

@login_required
def calendar_view(request):
    """Allows people to view their updated calendar schedule."""
    template = loader.get_template('calendar.html')
    context = {'user_email': request.user.email}
    return HttpResponse(template.render(context, request))

@login_required
def authorize(request):
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
    state = request.session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = _build_full_view_url(request, 'oauth2callback')
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    request.session['credentials'] = _credentials_to_dict(credentials)
    return HttpResponseRedirect(request.session['endurl'])


def _credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def _unpack_form_data(request):
    return {
        'name': request.POST['name'],
        'frequency': request.POST['frequency'],
        'period': request.POST['period'],
        'duration': request.POST['duration'],
        'timeunit': request.POST['timeunit'],
        'timerange': request.POST['timerange']
    }


def _get_rescheduling_info(request):
    credentials = Credentials(**request.session['credentials'])
    ids_and_titles, event_map = get_events_current_day(credentials)
    request.session['credentials'] = _credentials_to_dict(credentials)
    request.session['event_map'] = event_map
    return ids_and_titles


def _build_full_view_url(request, view):
    return 'http://' + request.environ['HTTP_HOST'] + reverse(view)
