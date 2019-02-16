from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange

# Authentication information
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Periods & timeunits
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"
HOURS, MINUTES = "HOURS", "MINUTES"

# Basic time constants
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# Arbitrary limit on the number of months scheduled when period is months.
MONTHS_TO_SCHEDULE = 3

# Bounding hours between which events can be scheduled each day (military time)
DAY_START_TIME = 8
DAY_END_TIME = 0


def make_schedule(form_data):
    service = get_credentials()
    events = schedule_events_for_multiple_periods(form_data, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


def schedule_events_for_multiple_periods(form_data, service):
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    localtz = get_local_timezone(service)
    period_start_time = get_next_day_start(datetime.now(localtz))
    period_end_time = get_period_end_time(period, period_start_time)
    event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    num_periods = get_number_periods(period, datetime.now(localtz))

    events = []
    for i in range(num_periods):
        events_for_single_period = schedule_events_for_single_period(service, form_data, localtz, period_start_time,
                                                                     period_end_time, event_start_time_max)
        if not events_for_single_period: return None
        else: events.extend(events_for_single_period)
        period_start_time = get_next_period_start_time(period, period_start_time)
        period_end_time = get_period_end_time(period, period_start_time)
        event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    return events


def schedule_events_for_single_period(service, form_data, localtz, period_start_time,
                                      period_end_time, event_start_time_max):
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    busy_times = get_busy_times(service, period_start_time, period_end_time)
    event_start_time = period_start_time
    event_index = 0
    events = []
    for i in range(frequency):
        if event_start_time > event_start_time_max: return None
        success, start_time, end_time = get_time_for_single_event(busy_times, localtz, duration, timeunit,
                                                                  event_start_time, event_start_time_max, event_index)
        if not success: return None
        events.append(create_event(name, start_time, end_time))
        event_start_time = get_next_event_start_time(period, start_time, end_time)
        event_index = update_event_index(busy_times, event_start_time, event_index)
    return events


def get_time_for_single_event(busy_times, localtz, duration, timeunit, start, start_time_max, event_index):
    end = increment_time(start, timeunit, duration)
    end_of_day = get_day_end_datetime(start)
    while (event_index < len(busy_times) and start <= start_time_max and
           conflicts(start, end, busy_times[event_index])):
        start = parse(busy_times[event_index]['end']).astimezone(localtz)
        end = increment_time(start, timeunit, duration)
        event_index += 1
        if end > end_of_day:
            start = make_start_time(end_of_day)
            end = increment_time(start, timeunit, duration)
            end_of_day = get_day_end_datetime(start)
            event_index = update_event_index(busy_times, start, event_index)
    search_successful = start <= start_time_max
    return search_successful, start, end


def get_number_periods(period, day):
    if period == DAY: return get_days_left_in_week(day) - 1
    elif period == WEEK: return get_weeks_left_in_month(day)
    elif period == MONTH: return MONTHS_TO_SCHEDULE


def get_next_period_start_time(period, period_start_time):
    if period == DAY: return get_next_day_start(period_start_time)
    elif period == WEEK: return get_next_week_start(period_start_time)
    elif period == MONTH: return get_next_month_start(period_start_time)


def get_period_end_time(period, period_start_time):
    if period == DAY: return get_end_of_day(period_start_time)
    elif period == WEEK: return get_end_of_week(period_start_time)
    elif period == MONTH: return get_end_of_month(period_start_time)


def get_next_event_start_time(period, start_time, time_last_event_was_scheduled):
    if period == DAY: return time_last_event_was_scheduled
    elif period == WEEK: return get_next_day_start(start_time)
    elif period == MONTH: return get_next_week_start(start_time)


def update_event_index(busy_times, event_start_time, event_index):
    while event_index < len(busy_times) and parse(busy_times[event_index]['end']) < event_start_time:
        event_index += 1
    return event_index


def get_day_end_datetime(day):
    hours_to_add = ((DAY_END_TIME + HOURS_IN_DAY) - DAY_START_TIME) % HOURS_IN_DAY
    return make_start_time(day) + timedelta(hours=hours_to_add)


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


def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)


def increment_time(day, timeunit, duration):
    if timeunit == HOURS: return day + timedelta(hours=duration)
    elif timeunit == MINUTES: return day + timedelta(minutes=duration)


def decrement_time(day, timeunit, duration):
    if timeunit == HOURS: return day - timedelta(hours=duration)
    elif timeunit == MINUTES: return day - timedelta(minutes=duration)


def make_midnight(day):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)


def make_start_time(day):
    return day.replace(hour=DAY_START_TIME, minute=0, second=0, microsecond=0)


def get_next_day_start(day):
    return make_start_time(get_end_of_day(day))


def get_next_week_start(day):
    return make_start_time(get_end_of_week(day))


def get_next_month_start(day):
    return make_start_time(get_end_of_month(day))


def get_end_of_day(day):
    next_day = (day + timedelta(days=1))
    return make_midnight(next_day)


def get_end_of_week(day):
    next_week = (day + timedelta(days=get_days_left_in_week(day)))
    return make_midnight(next_week)


def get_end_of_month(day):
    next_month = (day + timedelta(days=get_days_left_in_month(day)))
    return make_midnight(next_month)


def get_days_left_in_week(day):
    # Includes the inputted day
    day_index = (day.weekday() + 1) % DAYS_IN_WEEK
    return DAYS_IN_WEEK - day_index


def get_days_left_in_month(day):
    # Includes the inputted day
    days_in_month = monthrange(day.year, day.month)[1]
    return days_in_month - day.day + 1


def get_weeks_left_in_month(day):
    last_sunday = get_last_sunday_in_month(day)
    if day.day >= last_sunday.day: return 0
    return ((last_sunday.day - day.day - 1) // DAYS_IN_WEEK) + 1


def get_last_sunday_in_month(day):
    end_of_month = get_end_of_month(day)
    return end_of_month - timedelta(days=(end_of_month.weekday() + 1))


def unpack_form(form_data):
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    timerange = form_data['timerange']
    return name, frequency, period, duration, timeunit, timerange