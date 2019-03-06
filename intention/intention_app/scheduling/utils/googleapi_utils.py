"""Module to interface with Google calendar API.

Handles all requests and responses with Google Cal API.

Exported Functions
------------------
get_service()
get_localtz(service, cid='primary')
get_busy_ranges(service, timeMin, timeMax, cid='primary')
get_events_in_range(service, localtz, cid='primary')
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
    """Returns service object to make Google Calendar API requests."""
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def get_localtz(service, cid='primary'):
    """Returns timezone associated with user calendar."""
    calendar = service.calendars().get(calendarId=cid).execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)


def get_busy_ranges(service, timeMin, timeMax, cid='primary'):
    """Returns free/busy information for user calendar."""
    params = {
        'timeMin': timeMin.isoformat(),
        'timeMax': timeMax.isoformat(),
        'items': [{'id': cid}],
    }
    busy_ranges = service.freebusy().query(body=params).execute()
    return busy_ranges['calendars'][cid]['busy']


def get_events_in_range(service, timeMin, timeMax, cid='primary'):
    """Returns ids and titles of events in user calendar from start hour to end hour of current day."""
    events = []
    page_token = None
    while True:
        events_list = service.events().list(calendarId=cid, pageToken=page_token, singleEvents=True, showDeleted=False,
                                            maxResults=1000, timeMin=timeMin.isoformat(), timeMax=timeMax.isoformat()).execute()
        for event in events_list['items']:
            event_id = event['id']
            event_summary = event['summary']
            event_start = event['start']['dateTime']
            events.append((event_id, event_summary, event_start))
        page_token = events_list.get('nextPageToken')
        if not page_token:
            break
    events.sort(key=lambda x : x[2]) # sort events by start time.
    ids_and_titles = [(event[0], event[1]) for event in events]
    return ids_and_titles


def create_event(name, start, end):
    """Returns body for API request to insert new event."""
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
