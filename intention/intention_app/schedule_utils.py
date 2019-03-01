from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange
import numpy as np

# Authentication information
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Basic time constants
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# Arbitrary limit on the number of months scheduled when period is months.
MONTHS_TO_SCHEDULE = 3

# Bounding hours between which events can be scheduled each day
DAY_START_TIME = 8
DAY_END_TIME = 1

# Periods, timeunits, & timeranges
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"
HOURS, MINUTES = "HOURS", "MINUTES"
MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"

# Timerange hours
MORNING_HOURS = {'start': DAY_START_TIME, 'end': 12}
AFTERNOON_HOURS = {'start': 12, 'end': 18}
EVENING_HOURS = {'start': 18, 'end': DAY_END_TIME}

# Timezones
utc = timezone('UTC')

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


def get_number_periods(period, day, localtz):
    if period == DAY: return get_days_left_in_week(day)
    elif period == WEEK: return get_weeks_left_in_month(day, localtz)
    elif period == MONTH: return MONTHS_TO_SCHEDULE


def get_multi_period_end_time(period, timerange, day, localtz):
    if period == DAY: return get_end_of_week(day, timerange, localtz)
    elif period == WEEK: return get_end_of_month(day, timerange, localtz)
    elif period == MONTH: return get_end_of_quarter(day, timerange, localtz)


def get_next_period_start_time(period, timerange, period_start_time, localtz):
    if period == DAY: return get_start_of_next_day(period_start_time, timerange, localtz)
    elif period == WEEK: return get_start_of_next_week(period_start_time, timerange, localtz)
    elif period == MONTH: return get_start_of_next_month(period_start_time, timerange, localtz)


def get_period_end_time(period, timerange, period_start_time, localtz):
    if period == DAY: return get_end_of_day(period_start_time, timerange)
    elif period == WEEK: return get_end_of_week(period_start_time, timerange, localtz)
    elif period == MONTH: return get_end_of_month(period_start_time, timerange, localtz)


def get_next_event_start_time(period, timerange, start_time, time_last_event_was_scheduled, localtz):
    if period == DAY: return time_last_event_was_scheduled
    elif period == WEEK: return get_start_of_next_day(start_time, timerange, localtz)
    elif period == MONTH: return get_start_of_next_week(start_time, timerange, localtz)


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


def get_start_of_day(day, timerange):
    return make_start_time(day, timerange)


def get_start_of_next_day(day, timerange, localtz):
    if day.hour < DAY_START_TIME: return make_start_time(day, timerange)
    else: return make_start_time(get_next_day(day, localtz), timerange)


def get_start_of_next_week(day, timerange, localtz):
    return make_start_time(get_next_week(day, localtz), timerange)


def get_start_of_next_month(day, timerange, localtz):
    return make_start_time(get_next_month(day, localtz), timerange)


def get_end_of_day(day, timerange):
    return make_end_time(day, timerange)


def get_end_of_week(day, timerange, localtz):
    last_day_of_week = get_next_week(day, localtz) - timedelta(days=1)
    return make_end_time(last_day_of_week, timerange)


def get_end_of_month(day, timerange, localtz):
    last_day_of_month = get_next_month(day, localtz) - timedelta(days=1)
    return make_end_time(last_day_of_month, timerange)


def get_end_of_quarter(day, timerange, localtz):
    last_day_of_quarter = get_next_quarter(day, localtz) - timedelta(days=1)
    return make_end_time(last_day_of_quarter, timerange)


def get_next_day(day, localtz):
    return (day.astimezone(utc) + timedelta(days=1)).astimezone(localtz)


def get_next_week(day, localtz):
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_week(day))).astimezone(localtz)


def get_next_month(day, localtz):
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_month(day))).astimezone(localtz)


def get_next_quarter(day, localtz):
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_quarter(day))).astimezone(localtz)


def get_days_left_in_week(day):
    # Includes the inputted day
    day_index = (day.weekday() + 1) % DAYS_IN_WEEK
    return DAYS_IN_WEEK - day_index


def get_days_left_in_month(day):
    # Includes the inputted day
    days_in_month = monthrange(day.year, day.month)[1]
    return days_in_month - day.day + 1


def get_days_left_in_quarter(day):
    days_left = get_days_left_in_month(day)
    days_left += monthrange(day.year, day.month + 1)[1]
    days_left += monthrange(day.year, day.month + 2)[1]
    return days_left


def get_weeks_left_in_month(day, localtz):
    last_sunday = get_last_sunday_in_month(day, localtz)
    if day.day >= last_sunday.day: return 0
    return ((last_sunday.day - day.day - 1) // DAYS_IN_WEEK) + 1


def get_last_sunday_in_month(day, localtz):
    end_of_month = get_next_month(day, localtz)
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


def consolidate_busy_times(period, period_start_time, period_end_time, localtz, busy_times):
    minutes_in_period = get_minutes_in_period(period)
    minute_map = make_minute_map(period, minutes_in_period)
    minute_map_filled = consolidate(busy_times, localtz, period_start_time, minute_map, minutes_in_period)
    return convert_map_to_times(period_start_time, period_end_time, minute_map_filled)


def get_minutes_in_period(period):
    if period == DAY: return MINUTES_IN_HOUR * HOURS_IN_DAY
    elif period == WEEK: return MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_WEEK
    elif period == MONTH: return None # TODO: Decide on strategy for month.


def make_minute_map(period, minutes_in_period):
    if period == DAY: return np.ones(minutes_in_period, dtype=bool)
    elif period == WEEK: return np.ones(minutes_in_period, dtype=bool)
    elif period == MONTH: return None # TODO: Decide on strategy for month.


def minutes_between(start_time, end_time, localtz):
    minutes = int((end_time - start_time).total_seconds()) // 60
    st_loc = localtz.localize(start_time.replace(tzinfo=None))
    et_loc = localtz.localize(end_time.replace(tzinfo=None))
    if not isdst(st_loc) and isdst(et_loc): return minutes + 60
    elif isdst(st_loc) and not isdst(et_loc): return minutes - 60
    else: return minutes


def isdst(dt):
    return bool(dt.dst())


def consolidate(busy_times, localtz, period_start_time, minute_map, minutes_in_period):
    for i in range(len(busy_times)):
        busy_start, busy_end = get_busy_time_range(busy_times, i, localtz)
        start_minute = minutes_between(period_start_time, busy_start, localtz) % minutes_in_period
        end_minute = minutes_between(period_start_time, busy_end, localtz) % minutes_in_period
        if end_minute < start_minute:
            minute_map[start_minute:] = False
            minute_map[:end_minute] = False
        else:
            minute_map[start_minute:end_minute] = False
    return minute_map


def convert_map_to_times(period_start_time, period_end_time, minute_map_filled):
    busy_minutes = np.where(minute_map_filled == False)[0]
    busy_start = busy_minutes[0]
    busy_end = busy_minutes[0]
    busy_times = []
    for i in range(1, len(busy_minutes)):
        if busy_minutes[i] - busy_minutes[i-1] != 1:
            busy_end = busy_minutes[i-1] + 1
            busy_times.append(create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time))
            busy_start = busy_minutes[i]
    if busy_end != busy_minutes[-1] + 1:
        busy_end = busy_minutes[-1] + 1
        busy_times.append(create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time))
    return busy_times


def create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time):
    start_time = period_start_time + timedelta(minutes=int(busy_start))
    end_time = period_start_time + timedelta(minutes=int(busy_end))
    if start_time < period_start_time and end_time > period_end_time:
        start_time -= timedelta(days=1)
        end_time -= timedelta(days=1)
    return {
        'start': start_time.isoformat(),
        'end': end_time.isoformat()
    }


def copy_events_for_each_period(events, period, period_start_time, name, localtz):
    num_periods = get_number_periods(period, period_start_time, localtz)
    all_events = events.copy()
    for event in events:
        busy_start = parse(event['start']['dateTime'])
        busy_end = parse(event['end']['dateTime'])
        for i in range(1, num_periods):
            if period == "DAY":
                new_start = busy_start + timedelta(days=i)
                new_end = busy_end + timedelta(days=i)
                all_events.append(create_event(name, new_start, new_end))
            if period == "WEEK":
                new_start = busy_start + timedelta(weeks=i)
                new_end = busy_end + timedelta(weeks=i)
                all_events.append(create_event(name, new_start, new_end))
            if period == "MONTH": pass # TODO: Decide on strategy for month.
    return all_events
