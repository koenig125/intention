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

DAY_START_TIME = 8
DAYS_IN_WEEK = 7


def make_schedule(form_data):
    service = get_credentials()
    events = schedule_events(form_data, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def schedule_events(form_data, service):
    name, frequency, period, duration, timeunit = unpack_form(form_data)
    localtz = get_local_timezone(service)

    event_start_time = get_next_day_start(localtz, datetime.utcnow())
    event_end_time_max = get_event_end_time_max(period, localtz, event_start_time)
    event_start_time_max = decrement_time(event_end_time_max, timeunit, duration)

    if period == "DAY": return schedule_day(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max)
    elif period == "WEEK": return schedule_week(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max)
    elif period == "MONTH": return schedule_month(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max)


def schedule_day(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max):
    days_left_in_week = get_days_left_in_week(datetime.utcnow()) - 1
    timeunit = form_data['timeunit']
    duration = int(form_data['duration'])
    events = []
    for i in range(days_left_in_week):
        events_for_single_day = map_events_to_times(service, form_data, localtz, event_start_time,
                                                    event_end_time_max, event_start_time_max)
        if not events_for_single_day: return None
        else: events.extend(events_for_single_day)
        event_start_time += timedelta(days=1)
        event_end_time_max = get_end_of_day(localtz, event_start_time)
        event_start_time_max = decrement_time(event_end_time_max, timeunit, duration)
    return events


def schedule_week(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max):
    weeks_left_in_month = get_weeks_left_in_month(localtz, datetime.utcnow())
    timeunit = form_data['timeunit']
    duration = int(form_data['duration'])
    events = []
    for i in range(weeks_left_in_month):
        events_for_single_week = map_events_to_times(service, form_data, localtz, event_start_time,
                                                     event_end_time_max, event_start_time_max)
        if not events_for_single_week: return None
        else: events.extend(events_for_single_week)
        event_start_time = get_next_sunday_start(localtz, event_start_time)
        event_end_time_max = get_end_of_week(localtz, event_start_time)
        event_start_time_max = decrement_time(event_end_time_max, timeunit, duration)
    return events


def schedule_month(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max):
    return map_events_to_times(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max)


def map_events_to_times(service, form_data, localtz, event_start_time, event_end_time_max, event_start_time_max):
    name, frequency, period, duration, timeunit = unpack_form(form_data)
    events = []
    for i in range(frequency):
        if event_start_time > event_start_time_max: return None
        busy_times = get_busy_times(service, event_start_time, event_end_time_max)
        success, start_time, end_time, event_index = get_first_free_time(busy_times, duration, timeunit, event_start_time,
                                                                         event_start_time_max, localtz, 0)
        if not success: return None
        events.append(create_event(name, start_time, end_time))
        event_start_time = update_event_start_time(period, start_time, end_time, localtz)
    return events


def get_first_free_time(busy_times, duration, timeunit, start_time, last_time_event_can_be_scheduled, localtz, event_index):
    end_time = increment_time(start_time, timeunit, duration)
    while (event_index < len(busy_times) and start_time <= last_time_event_can_be_scheduled and
           conflicts(start_time, end_time, busy_times[event_index])):
        if start_time.date() < end_time.date(): # if end_time extends past midnight, skip to next day (for now).
            start_time = get_next_day_start(localtz, start_time)
            end_time = increment_time(start_time, timeunit, duration)
        else:
            start_time += timedelta(minutes=1)
            end_time += timedelta(minutes=1)
        if start_time >= parse(busy_times[event_index]['end']):
            event_index += 1
    search_successful = start_time <= last_time_event_can_be_scheduled
    return search_successful, start_time, end_time, event_index


def conflicts(start_time, end_time, existing_event):
    event_start = parse(existing_event['start'])
    event_end = parse(existing_event['end'])
    return (event_start <= start_time < event_end or
            event_start < end_time <= event_end or
            (start_time < event_start and end_time > event_end))


def get_busy_times(service, start, end):
    params = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": "primary"}],
    }
    busy_times = service.freebusy().query(body=params).execute()
    return busy_times["calendars"]["primary"]["busy"]


def create_event(name, start_time, end_time):
    return {
            'summary': name,
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
        }


def add_events_to_calendar(service, events):
    for event in events:
        service.events().insert(calendarId='primary', body=event).execute()


def update_event_start_time(period, start_time, end_time, localtz):
    if period == "DAY": return end_time
    elif period == "WEEK": return get_next_day_start(localtz, start_time)
    elif period == "MONTH": return get_next_sunday_start(localtz, start_time)


def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)


def increment_time(day, timeunit, duration):
    if timeunit == "HOURS": return day + timedelta(hours=duration)
    elif timeunit == "MINUTES": return day + timedelta(minutes=duration)


def decrement_time(day, timeunit, duration):
    if timeunit == "HOURS": return day - timedelta(hours=duration)
    elif timeunit == "MINUTES": return day - timedelta(minutes=duration)


def get_next_day_start(localtz, day):
    return get_end_of_day(localtz, day) + timedelta(hours=DAY_START_TIME)


def get_next_sunday_start(localtz, day):
    return get_end_of_week(localtz, day) + timedelta(hours=DAY_START_TIME)


def get_end_of_day(localtz, day):
    next_day = (day + timedelta(days=1)).astimezone(localtz)
    return make_midnight(next_day)


def get_end_of_week(localtz, day):
    next_week = (day + timedelta(days=get_days_left_in_week(day))).astimezone(localtz)
    return make_midnight(next_week)


def get_end_of_month(localtz, day):
    next_month = (day + timedelta(days=get_days_left_in_month(day))).astimezone(localtz)
    return make_midnight(next_month)


def get_event_end_time_max(period, localtz, event_start_time):
    if period == "DAY": return get_end_of_day(localtz, event_start_time)
    elif period == "WEEK": return get_end_of_week(localtz, event_start_time)
    elif period == "MONTH": return get_end_of_month(localtz, event_start_time)


def get_days_left_in_week(day):
    # days left in week including the inputted day
    day_index = (day.weekday() + 1) % DAYS_IN_WEEK
    return DAYS_IN_WEEK - day_index


def get_days_left_in_month(day):
    # days left in month, including the inputted day
    days_in_month = monthrange(day.year, day.month)[1]
    return days_in_month - day.day + 1


def get_weeks_left_in_month(localtz, day):
    last_sunday = get_last_sunday_in_month(localtz, day)
    if day.day >= last_sunday.day: return 0
    return ((last_sunday.day - day.day - 1) // 7) + 1


def get_last_sunday_in_month(localtz, day):
    end_of_month = get_end_of_month(localtz, day)
    print(end_of_month)
    return end_of_month - timedelta(days=(end_of_month.weekday() + 1))


def make_midnight(day):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)


def unpack_form(form_data):
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    return name, frequency, period, duration, timeunit