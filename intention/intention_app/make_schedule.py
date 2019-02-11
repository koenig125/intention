from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

def make_schedule(form_data):
	service = get_credentials()
	add_events_to_calendar(form_data, service)

def add_events_to_calendar(form_data, service):
	event = {
		'summary': form_data['name'],
		'start': {
			'dateTime': '2019-02-11T12:00:00-08:00',
		},
		'end': {
			'dateTime': '2019-02-11T13:00:00-08:00',
		},
	}
	service.events().insert(calendarId='primary', body=event).execute()

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server()
    service = build('calendar', 'v3', credentials=creds)
    return service