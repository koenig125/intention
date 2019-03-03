"""Module to provide basic scheduling functions."""

from dateutil.parser import parse
from intention_app.scheduling.utils.datetime_utils import *


def unpack_form(form_data):
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    timerange = form_data['timerange']
    return name, frequency, period, duration, timeunit, timerange


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
    return make_start_hour(day, timerange), make_end_hour(day, timerange)


def in_timerange(event_start, event_end, range_start, range_end):
    return (range_start <= event_start <= range_end and
            range_start <= event_end <= range_end)