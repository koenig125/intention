from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, date, time, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']


def make_schedule(form_data):
	service = get_credentials()
	add_events_to_calendar(form_data, service)


def get_busy_times(service):
    start = datetime.utcnow()
    dayIndex = (date.today().weekday() + 1) % 7
    sunday = start + timedelta(days=(7 - dayIndex))
    end = sunday.replace(hour=0, minute=0, second=0, microsecond=0)
    params = {
        "timeMin": start.isoformat() + 'Z',
        "timeMax": end.isoformat() + 'Z',
        "items": [{"id": "primary"}],
    }
    busy_times = service.freebusy().query(body=params).execute()
    print(busy_times)
    return busy_times["calendars"]["primary"]


def get_first_free_time(busy_times):
    return datetime.utcnow() + timedelta(hours = 3)


def add_events_to_calendar(form_data, service):
    busy_times = get_busy_times(service)
    start_time = get_first_free_time(busy_times)
    end_time = start_time + timedelta(hours=1)
    event = {
		'summary': form_data['name'],
		'start': {
			'dateTime': start_time.isoformat() + 'Z',
		},
		'end': {
			'dateTime': end_time.isoformat() + 'Z',
		},
	}
    service.events().insert(calendarId='primary', body=event).execute()


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server()
    service = build('calendar', 'v3', credentials=creds)
    return service