"""Module to interface with Google calendar API.

Handles all requests and responses with Google Cal API.

Exported Functions
------------------
get_localtz(credentials, cid='primary')
add_events_to_calendar(credentials, events, cid='primary')
update_events_in_calendar(credentials, events, cid="primary")
get_calendars(credentials)
get_freebusy_in_range(credentials, timeMin, timeMax, cid='primary')
get_events_in_range(credentials, timeMin, timeMax, cid='primary')
create_event(event_name, start_time, end_time)
"""

from googleapiclient.discovery import build
from pytz import timezone

API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


def get_localtz(credentials, cid='primary'):
    """Returns timezone associated with user calendar."""
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    calendar = service.calendars().get(calendarId=cid).execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)


def add_events_to_calendar(credentials, events, cid='primary'):
    """Makes API requests to insert new events into user calendar."""
    for event in events:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        service.events().insert(calendarId=cid, body=event).execute()


def update_events_in_calendar(credentials, events):
    """Makes API requests to update events into user calendar."""
    cid = None
    for event in events:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        cid = event['organizer']['email']
        service.events().update(calendarId=cid, eventId=event['id'], body=event).execute()
    return cid


def get_calendars(credentials):
    """Returns list of user calendars."""
    calendars = []
    page_token = None
    while True:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        calendars.extend(calendar_list['items'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return calendars


def get_freebusy_in_range(credentials, timeMin, timeMax, calendars=['primary']):
    """Returns free/busy information for user calendar between timeMin and timeMax."""
    freebusy = []
    for cid in calendars:
        params = {
            'timeMin': timeMin.isoformat(),
            'timeMax': timeMax.isoformat(),
            'items': [{'id': cid}],
        }
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        busy_ranges = service.freebusy().query(body=params).execute()
        freebusy.extend(busy_ranges['calendars'][cid]['busy'])
    freebusy.sort(key=lambda x : x['start'])
    return freebusy


def get_events_in_range(credentials, timeMin, timeMax, calendars=['primary']):
    """Returns events in user calendar between timeMin and timeMax."""
    events = []
    for cid in calendars:
        page_token = None
        while True:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
            events_list = service.events().list(calendarId=cid, pageToken=page_token, singleEvents=True, showDeleted=False,
                                                maxResults=1000, timeMin=timeMin.isoformat(), timeMax=timeMax.isoformat()).execute()
            events.extend(events_list['items'])
            page_token = events_list.get('nextPageToken')
            if not page_token:
                break
    events = [x for x in events if 'dateTime' in x['start']]
    events.sort(key=lambda x : x['start']['dateTime'])
    return events


def create_event(event_name, start_time, end_time):
    """Returns body for API request to insert new event."""
    return {
            'summary': event_name,
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
        }
