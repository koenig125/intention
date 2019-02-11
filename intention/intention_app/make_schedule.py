from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone

CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


def make_schedule(form_data):
    service = get_credentials()
    add_events_to_calendar(form_data, service)


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def add_events_to_calendar(form_data, service):
    duration = int(form_data['length'])
    localtz = get_local_timezone(service)
    busy_times = get_busy_times(service, localtz)
    start_time, end_time = get_first_free_time(busy_times, localtz, duration)
    event = {
		'summary': form_data['name'],
		'start': {
			'dateTime': start_time.isoformat(),
		},
		'end': {
			'dateTime': end_time.isoformat(),
		},
	}
    service.events().insert(calendarId='primary', body=event).execute()


def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    tz_name = calendar['timeZone']
    return timezone(tz_name)


def get_start_next_day(localtz):
    tomorrow = (datetime.utcnow() + timedelta(days=1)).astimezone(localtz)
    start_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=8)
    return start_time


def get_busy_times(service, localtz):
    start = get_start_next_day(localtz)
    dayIndex = (start.weekday() + 1) % 7
    sunday = start + timedelta(days=(7 - dayIndex))
    end = sunday.replace(hour=0, minute=0, second=0, microsecond=0)
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": "primary"}],
    }
    busy_times = service.freebusy().query(body=params).execute()
    return busy_times["calendars"]["primary"]["busy"]


def get_first_free_time(busy_times, localtz, duration):
    start_time = get_start_next_day(localtz)
    end_time = start_time + timedelta(hours=duration)
    event_index = 0
    while (event_index < len(busy_times) and
           conflicts(start_time, start_time + timedelta(hours=1), busy_times[event_index])):
        start_time += timedelta(hours=1)
        end_time += timedelta(hours=1)
        if start_time > parse(busy_times[event_index]['end']):
            event_index += 1
    return start_time, end_time


def conflicts(start_time, end_time, existing_event):
    event_start = parse(existing_event['start'])
    event_end = parse(existing_event['end'])
    return (event_start <= start_time < event_end or
            event_start < end_time <= event_end)