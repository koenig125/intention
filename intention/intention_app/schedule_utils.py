from __future__ import print_function
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service

def get_first_available_time(now, timerange):
    next_hour = make_next_hour(now)
    range_start, range_end = get_desired_time_range(now, timerange)
    if next_hour > range_end: return range_start + timedelta(hours=HOURS_IN_DAY)
    elif next_hour < range_start: return range_start
    else: return next_hour


def get_number_periods(period, day):
    if period == DAY: return get_days_left_in_week(day)
    elif period == WEEK: return get_weeks_left_in_month(day)
    elif period == MONTH: return MONTHS_TO_SCHEDULE


def get_next_period_start_time(period, timerange, period_start_time):
    if period == DAY: return get_start_of_next_day(period_start_time, timerange)
    elif period == WEEK: return get_start_of_next_week(period_start_time, timerange)
    elif period == MONTH: return get_start_of_next_month(period_start_time, timerange)


def get_period_end_time(period, timerange, period_start_time):
    if period == DAY: return get_end_of_day(period_start_time, timerange)
    elif period == WEEK: return get_end_of_week(period_start_time, timerange)
    elif period == MONTH: return get_end_of_month(period_start_time, timerange)


def get_next_event_start_time(period, timerange, start_time, time_last_event_was_scheduled):
    if period == DAY: return time_last_event_was_scheduled
    elif period == WEEK: return get_start_of_next_day(start_time, timerange)
    elif period == MONTH: return get_start_of_next_week(start_time, timerange)


def update_event_index(busy_times, next_start_time, event_index):
    while event_index < len(busy_times) and parse(busy_times[event_index]['end']) <= next_start_time:
        event_index += 1
    return event_index


def get_busy_time_range(busy_times, event_index, localtz):
    if event_index >= len(busy_times): return None, None
    busy_start = parse(busy_times[event_index]['start']).astimezone(localtz)
    busy_end = parse(busy_times[event_index]['end']).astimezone(localtz)
    return busy_start, busy_end


def conflicts(event_start, event_end, busy_start, busy_end):
    return (busy_start <= event_start < busy_end or
            busy_start < event_end <= busy_end or
            (event_start < busy_start and event_end > busy_end))


def get_desired_time_range(day, timerange):
    return make_start_time(day, timerange), make_end_time(day, timerange)


def in_timerange(event_start, event_end, range_start, range_end):
    return (range_start <= event_start <= range_end and
            range_start <= event_end <= range_end)


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


def get_next_day(day):
    return day + timedelta(days=1)


def get_next_week(day):
    return day + timedelta(days=get_days_left_in_week(day))


def get_next_month(day):
    return day + timedelta(days=get_days_left_in_month(day))


def get_end_of_day(day, timerange):
    return make_end_time(day, timerange)


def get_end_of_week(day, timerange):
    last_day_of_week = get_next_week(day) - timedelta(days=1)
    return make_end_time(last_day_of_week, timerange)


def get_end_of_month(day, timerange):
    last_day_of_month = get_next_month(day) - timedelta(days=1)
    return make_end_time(last_day_of_month, timerange)


def get_start_of_day(day, timerange):
    return make_start_time(day, timerange)


def get_start_of_next_day(day, timerange):
    if day.hour < DAY_START_TIME: return make_start_time(day, timerange)
    else: return make_start_time(get_next_day(day), timerange)


def get_start_of_next_week(day, timerange):
    return make_start_time(get_next_week(day), timerange)


def get_start_of_next_month(day, timerange):
    return make_start_time(get_next_month(day), timerange)


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
    end_of_month = get_next_month(day)
    return end_of_month - timedelta(days=(end_of_month.weekday() + 1))


def make_start_time(day, timerange):
    start_time = DAY_START_TIME
    if timerange == MORNING: start_time = MORNING_HOURS['start']
    elif timerange == AFTERNOON: start_time = AFTERNOON_HOURS['start']
    elif timerange == EVENING: start_time = EVENING_HOURS['start']
    day_start = day.replace(hour=start_time, minute=0, second=0, microsecond=0)
    return day_start


def make_end_time(day, timerange):
    end_time = DAY_END_TIME
    if timerange == MORNING: end_time = MORNING_HOURS['end']
    elif timerange == AFTERNOON: end_time = AFTERNOON_HOURS['end']
    elif timerange == EVENING: end_time = EVENING_HOURS['end']
    day_end = day.replace(hour=end_time, minute=0, second=0, microsecond=0)
    if end_time == DAY_END_TIME and DAY_END_TIME < DAY_START_TIME:
        day_end += timedelta(hours=HOURS_IN_DAY)
    return day_end


def make_midnight(day):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)


def make_next_hour(day):
    return day.replace(hour=day.hour, minute=0, second=0, microsecond=0) + timedelta(hours=1)


def unpack_form(form_data):
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    timerange = form_data['timerange']
    return name, frequency, period, duration, timeunit, timerange