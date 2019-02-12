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
    success = add_events_to_calendar(form_data, service)
    return success


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def add_events_to_calendar(form_data, service):
    duration = int(form_data['duration'])
    frequency = int(form_data['frequency'])
    timeunit = form_data['timeunit']
    period = form_data['period']
    localtz = get_local_timezone(service)

    if period == "DAY": return schedule_day(service, form_data, frequency, duration, timeunit, localtz)
    elif period == "WEEK": return schedule_week(service, form_data, frequency, duration, timeunit, localtz)
    else: schedule_month()


def schedule_day(service, form_data, frequency, duration, timeunit, localtz):
    events = []
    start_next_day = get_next_day_8am(localtz, datetime.utcnow())
    end_next_day = get_end_of_day(localtz, start_next_day)


    for i in range(frequency):
        busy_times = get_busy_times(service, start_next_day, end_next_day)
        success, start_time, end_time = get_first_free_time(busy_times, duration, timeunit, start_next_day,
                                                            end_next_day, localtz)
        if not success: return False  # Schedule did not have room for candidate event. Abort.
        event = {
            'summary': form_data['name'],
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
        }
        events.append(event)
        start_next_day = get_next_day_8am(localtz, start_time)
        end_next_day = get_end_of_day(localtz, start_next_day)

    for event in events:
        service.events().insert(calendarId='primary', body=event).execute()
    return True


def schedule_week(service, form_data, frequency, duration, timeunit, localtz):
    events = []
    start_next_day = get_next_day_8am(localtz, datetime.utcnow())
    last_possible_day = get_end_of_week(start_next_day)

    for i in range(frequency):
        if start_next_day > last_possible_day:
            return False # Not enough days in week to schedule all instances of intention. Abort.
        busy_times = get_busy_times(service, start_next_day, last_possible_day)
        success, start_time, end_time = get_first_free_time(busy_times, duration, timeunit, start_next_day,
                                                            last_possible_day, localtz)
        if not success: return False # Schedule did not have room for candidate event. Abort.
        event = {
            'summary': form_data['name'],
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
        }
        events.append(event)
        start_next_day = get_next_day_8am(localtz, start_time) # start_time for now due to edge case of end_time=midnight

    for event in events:
        service.events().insert(calendarId='primary', body=event).execute()
    return True


def schedule_month():
    return False


def get_busy_times(service, start, end):
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": "primary"}],
    }
    busy_times = service.freebusy().query(body=params).execute()
    return busy_times["calendars"]["primary"]["busy"]


def get_first_free_time(busy_times, duration, timeunit, start_time, last_possible_day, localtz):
    end_time = get_event_end_time(start_time, duration, timeunit)
    event_index = 0
    while (event_index < len(busy_times) and start_time < last_possible_day and
           conflicts(start_time, end_time, busy_times[event_index])):
        if start_time.date() < end_time.date(): # if end_time extends past midnight, skip to next day (for now).
            start_time = get_next_day_8am(localtz, start_time)
            end_time = get_event_end_time(start_time, duration, timeunit)
        else:
            start_time += timedelta(minutes=1)
            end_time += timedelta(minutes=1)
        if start_time >= parse(busy_times[event_index]['end']):
            event_index += 1
    search_successful = start_time < last_possible_day
    return search_successful, start_time, end_time


def get_event_end_time(start_time, duration, timeunit):
    if timeunit == "HOURS": return start_time + timedelta(hours=duration)
    elif timeunit == "MINUTES": return start_time + timedelta(minutes=duration)


def conflicts(start_time, end_time, existing_event):
    event_start = parse(existing_event['start'])
    event_end = parse(existing_event['end'])
    return (event_start <= start_time < event_end or
            event_start < end_time <= event_end or
            (start_time < event_start and end_time > event_end))


def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    tz_name = calendar['timeZone']
    return timezone(tz_name)


def get_next_day_8am(localtz, last_busy_day):
    return get_end_of_day(localtz, last_busy_day) + timedelta(hours=8)


def get_end_of_day(localtz, day):
    next_day = (day + timedelta(days=1)).astimezone(localtz)
    return make_midnight(next_day)


def get_end_of_week(current_day):
    next_sunday = current_day + timedelta(days=get_days_left_in_week(current_day))
    return make_midnight(next_sunday)


def get_days_left_in_week(day):
    dayIndex = (day.weekday() + 1) % 7
    return 7 - dayIndex


def make_midnight(day):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)