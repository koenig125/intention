from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange

CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
DAYS_IN_WEEK = 7


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
    elif period == "MONTH": return schedule_month(service, form_data, frequency, duration, timeunit, localtz)


def schedule_day(service, form_data, frequency, duration, timeunit, localtz):
    events = []
    days_left = get_days_left_in_week(datetime.utcnow()) - 1
    start_of_day = get_next_day_8am(localtz, datetime.utcnow())
    end_of_day = get_end_of_day(localtz, start_of_day)

    for i in range(days_left):
        busy_times = get_busy_times(service, start_of_day, end_of_day)
        event_start_time = start_of_day
        last_time_event_can_be_scheduled = decrement_duration(end_of_day, duration, timeunit)
        event_index = 0
        for j in range(frequency):
            success, start_time, end_time, event_index = get_first_free_time(busy_times, duration, timeunit,
                                            event_start_time, last_time_event_can_be_scheduled, localtz, event_index)
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
            event_start_time = end_time
        start_of_day += timedelta(days=1)
        end_of_day = get_end_of_day(localtz, start_of_day)

    add_events(service, events)
    return True


def schedule_week(service, form_data, frequency, duration, timeunit, localtz):
    events = []
    start_next_day = get_next_day_8am(localtz, datetime.utcnow())
    end_of_week = get_end_of_week(localtz, start_next_day)
    last_time_event_can_be_scheduled = decrement_duration(end_of_week, duration, timeunit)

    for i in range(frequency):
        if start_next_day > last_time_event_can_be_scheduled: return False
        busy_times = get_busy_times(service, start_next_day, end_of_week)
        success, start_time, end_time, event_index = get_first_free_time(busy_times, duration, timeunit, start_next_day,
                                                                         last_time_event_can_be_scheduled, localtz, 0)
        if not success: return False # Schedule did not have room for candidate event or reached end of week. Abort.
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

    add_events(service, events)
    return True


def schedule_month(service, form_data, frequency, duration, timeunit, localtz):
    events = []
    start_next_day = get_next_day_8am(localtz, datetime.utcnow())
    end_of_month = get_end_of_month(start_next_day)
    last_time_event_can_be_scheduled = decrement_duration(end_of_month, duration, timeunit)

    for i in range(frequency):
        if start_next_day > last_time_event_can_be_scheduled: return False
        busy_times = get_busy_times(service, start_next_day, end_of_month)
        success, start_time, end_time, event_index = get_first_free_time(busy_times, duration, timeunit, start_next_day,
                                                                         last_time_event_can_be_scheduled, localtz, 0)
        if not success: return False  # Schedule did not have room for candidate event or reached end of week. Abort.
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
        start_next_day = get_next_sunday_8am(localtz, start_time)  # start_time for now due to edge case of end_time=midnight

    add_events(service, events)
    return True


def get_busy_times(service, start, end):
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": "primary"}],
    }
    busy_times = service.freebusy().query(body=params).execute()
    return busy_times["calendars"]["primary"]["busy"]


def get_first_free_time(busy_times, duration, timeunit, start_time, last_time_event_can_be_scheduled, localtz, event_index):
    end_time = increment_duration(start_time, duration, timeunit)
    while (event_index < len(busy_times) and start_time <= last_time_event_can_be_scheduled and
           conflicts(start_time, end_time, busy_times[event_index])):
        if start_time.date() < end_time.date(): # if end_time extends past midnight, skip to next day (for now).
            start_time = get_next_day_8am(localtz, start_time)
            end_time = increment_duration(start_time, duration, timeunit)
        else:
            start_time += timedelta(minutes=1)
            end_time += timedelta(minutes=1)
        if start_time >= parse(busy_times[event_index]['end']):
            event_index += 1
    print("FROM GETFIRSTFREETIME")
    print(start_time)
    print(end_time)
    search_successful = start_time <= last_time_event_can_be_scheduled
    return search_successful, start_time, end_time, event_index


def conflicts(start_time, end_time, existing_event):
    event_start = parse(existing_event['start'])
    event_end = parse(existing_event['end'])
    return (event_start <= start_time < event_end or
            event_start < end_time <= event_end or
            (start_time < event_start and end_time > event_end))


def increment_duration(day, duration, timeunit):
    if timeunit == "HOURS": return day + timedelta(hours=duration)
    elif timeunit == "MINUTES": return day + timedelta(minutes=duration)


def decrement_duration(day, duration, timeunit):
    if timeunit == "HOURS": return day - timedelta(hours=duration)
    elif timeunit == "MINUTES": return day - timedelta(minutes=duration)


def add_events(service, events):
    for event in events:
        service.events().insert(calendarId='primary', body=event).execute()


def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    tz_name = calendar['timeZone']
    return timezone(tz_name)


def get_next_day_8am(localtz, day):
    return get_end_of_day(localtz, day) + timedelta(hours=8)


def get_next_sunday_8am(localtz, day):
    return get_end_of_week(localtz, day) + timedelta(hours=8)


def get_end_of_day(localtz, day):
    next_day = (day + timedelta(days=1)).astimezone(localtz)
    return make_midnight(next_day)


def get_end_of_week(localtz, day):
    next_week = (day + timedelta(days=get_days_left_in_week(day))).astimezone(localtz)
    return make_midnight(next_week)


def get_end_of_month(day):
    next_month = day + timedelta(days=get_days_left_in_month(day))
    return make_midnight(next_month)


def get_days_left_in_week(day):
    # days left in week including the parameter day
    # weekdays are 0-indexed starting from Monday
    # ie index(Sunday) = 6 and index(Monday) = 0
    day_index = (day.weekday() + 1) % DAYS_IN_WEEK
    return DAYS_IN_WEEK - day_index


def get_days_left_in_month(day):
    # days left in month, including the parameter day
    days_in_month = monthrange(day.year, day.month)[1]
    return days_in_month - day.day + 1


def make_midnight(day):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)