from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange
from .schedule_utils import *

# Authentication information
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Basic time constants
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


def make_schedule(form_data):
    service = get_credentials()
    events = schedule_events_for_multiple_periods(form_data, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True

def schedule_events_for_multiple_periods(form_data, service):
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    localtz = get_local_timezone(service)
    period_start_time = get_first_available_time(datetime.now(localtz), timerange)
    period_end_time = get_period_end_time(period, timerange, datetime.now(localtz))
    if period_start_time > period_end_time: return None # Triggered when can't schedule event by end of current day/week
    event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    num_periods = get_number_periods(period, period_start_time)

    events = []
    for i in range(num_periods):
        events_for_single_period = schedule_events_for_single_period(service, form_data, localtz, period_start_time,
                                                                     period_end_time, event_start_time_max)
        if not events_for_single_period: return None
        else: events.extend(events_for_single_period)
        period_start_time = get_next_period_start_time(period, timerange, period_start_time)
        period_end_time = get_period_end_time(period, timerange, period_start_time)
        event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    return events


def schedule_events_for_single_period(service, form_data, localtz, period_start_time,
                                      period_end_time, event_start_time_max):
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    range_start, range_end = get_desired_time_range(period_start_time, timerange)
    busy_times = get_busy_times(service, period_start_time, period_end_time)
    event_start_time = period_start_time
    event_index = 0
    events = []
    for i in range(frequency):
        if event_start_time > event_start_time_max: return None
        success, start_time, end_time = find_time_for_single_event(busy_times, localtz, duration, timeunit, range_start,
                                                        range_end, event_start_time, event_start_time_max, event_index)
        if not success: return None
        events.append(create_event(name, start_time, end_time))
        event_start_time = get_next_event_start_time(period, timerange, start_time, end_time)
        if period != DAY: range_start, range_end = get_desired_time_range(event_start_time, timerange)
        event_index = update_event_index(busy_times, event_start_time, event_index)
    return events


def find_time_for_single_event(busy_times, localtz, duration, timeunit, range_start,
                               range_end, event_start, max_start_time, event_index):
    busy_start, busy_end = get_busy_time_range(busy_times, event_index, localtz)
    event_end = increment_time(event_start, timeunit, duration)
    while (event_index < len(busy_times) and event_start <= max_start_time and
           (conflicts(event_start, event_end, busy_start, busy_end) or not
           in_timerange(event_start, event_end, range_start, range_end))):
        if event_end > range_end:
            range_start += timedelta(hours=HOURS_IN_DAY)
            range_end += timedelta(hours=HOURS_IN_DAY)
            event_start = range_start
            event_index = update_event_index(busy_times, range_start, event_index)
        else:
            event_start = busy_end
            event_index += 1
        event_end = increment_time(event_start, timeunit, duration)
        busy_start, busy_end = get_busy_time_range(busy_times, event_index, localtz)
    search_successful = event_start <= max_start_time and in_timerange(event_start, event_end, range_start, range_end)
    return search_successful, event_start, event_end