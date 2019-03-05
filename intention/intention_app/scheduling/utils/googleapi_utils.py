"""Module to interface with Google calendar API.

Handles all requests and responses with Google Cal API.

Exported Functions
------------------
get_service()
get_localtz(service, cid='primary')
get_busy_ranges(service, timeMin, timeMax, cid='primary')
create_event(name, start, end)
add_events_to_calendar(service, events, cid='primary')
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pytz import timezone

CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


def get_service():
    """Gets service object to make Google Calendar API requests."""
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def get_localtz(service, cid='primary'):
    """Gets timezone associated with user calendar."""
    calendar = service.calendars().get(calendarId=cid).execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)


def get_busy_ranges(service, timeMin, timeMax, cid='primary'):
    """Gets free/busy information for user calendar."""
    params = {
        'timeMin': timeMin.isoformat(),
        'timeMax': timeMax.isoformat(),
        'items': [{'id': cid}],
    }
    busy_ranges = service.freebusy().query(body=params).execute()
    return busy_ranges['calendars'][cid]['busy']


def create_event(name, start, end):
    """Creates body for API request to insert new event."""
    return {
            'summary': name,
            'start': {
                'dateTime': start.isoformat(),
            },
            'end': {
                'dateTime': end.isoformat(),
            },
        }


def add_events_to_calendar(service, events, cid='primary'):
    """Makes API requests to insert new events into user calendar."""
    for event in events:
        service.events().insert(calendarId=cid, body=event).execute()


def get_events_from_calendar(service, timeMin, timeMax, cid='primary'): 
    tasks = []
    page_token = None
    while True:
        events = service.events().list(calendarId=cid, pageToken=page_token, timeMin=timeMin, timeMax=timeMax).execute()
        for event in events['items']:
            # print(event.keys())
            event_summary = event.get('summary', "Untitled")
            print(event_summary)
            tasks.append(event_summary)
        page_token = events.get('nextPageToken')
        if not page_token:
            break
    return tasks
