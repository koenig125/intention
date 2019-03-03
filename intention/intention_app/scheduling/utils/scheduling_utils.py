"""Module to provide simple scheduling functions.

Determines period timeframes and provides simple scheduling functionality.
Periods are day, week, and month. Multi-periods are series of consecutive
periods - week, month, and quarter for day, week, and month, respectively.

Exported Functions
------------------
unpack_form(form_data)
get_start_time(curr_time, timerange)
get_number_periods(day, period, localtz)
get_timedelta_to_future_period(day, period, num_periods_in_future, localtz)
get_start_of_next_period(curr_period_start_time, period, timerange, localtz)
get_start_of_next_event(curr_event_start_time, last_scheduled_event_end_time, period, timerange, localtz)
get_end_of_multi_period(day, period, timerange, localtz)
get_end_of_period(period_start_time, period, timerange, localtz)
is_conflicting(range_start, range_end, event_start, event_end)
in_timerange(range_start, range_end, event_start, event_end)
update_index(index, events, threshold_time)
get_range_start_end(timerange, localtz)
"""

from intention_app.scheduling.utils.datetime_utils import *

# Length scheduled when period is months.
NUMBER_MONTHS_TO_SCHEDULE = 3


def unpack_form(form_data):
    """Returns each field required for scheduling in the django form."""
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    timerange = form_data['timerange']
    return name, frequency, period, duration, timeunit, timerange


def get_start_time(curr_time, timerange):
    """Returns first time available for scheduling within timerange."""
    next_hour = make_next_hour(curr_time)
    range_start, range_end = get_day_start_end_times(curr_time, timerange)
    if next_hour > range_end: return range_start + timedelta(days=1)
    elif next_hour < range_start: return range_start
    else: return next_hour


def get_number_periods(day, period, localtz):
    """Returns number of periods remaining in the current multi-period."""
    if period == DAY: return get_days_left_in_week(day)
    elif period == WEEK: return get_weeks_left_in_month(day, localtz)
    elif period == MONTH: return NUMBER_MONTHS_TO_SCHEDULE


def get_timedelta_to_future_period(day, period, num_periods, localtz):
    """Returns timedelta to increment day num_periods into the future."""
    if period == DAY: return timedelta(days=num_periods)
    elif period == WEEK: return timedelta(weeks=num_periods)
    elif period == MONTH: return get_month_timedelta(day, num_periods, localtz)


def get_start_of_next_period(curr_period_start_time, period, timerange, localtz):
    """Returns the first day of the next period set to start hour."""
    if period == DAY: return get_start_of_next_day(curr_period_start_time, timerange, localtz)
    elif period == WEEK: return get_start_of_next_week(curr_period_start_time, timerange, localtz)
    elif period == MONTH: return get_start_of_next_month(curr_period_start_time, timerange, localtz)


def get_start_of_next_event(curr_event_start_time, last_scheduled_event_end_time, period, timerange, localtz):
    """Returns the first day on which the next event can be scheduled set to start hour."""
    if period == DAY: return last_scheduled_event_end_time
    elif period == WEEK: return get_start_of_next_day(curr_event_start_time, timerange, localtz)
    elif period == MONTH: return get_start_of_next_week(curr_event_start_time, timerange, localtz)


def get_end_of_multi_period(day, period, timerange, localtz):
    """Returns the last day of the current multiperiod set to end hour."""
    if period == DAY: return get_end_of_week(day, timerange, localtz)
    elif period == WEEK: return get_end_of_month(day, timerange, localtz)
    elif period == MONTH: return get_end_of_quarter(day, timerange, localtz)


def get_end_of_period(period_start_time, period, timerange, localtz):
    """Returns the last day of the current period set to end hour."""
    if period == DAY: return get_end_of_day(period_start_time, timerange)
    elif period == WEEK: return get_end_of_week(period_start_time, timerange, localtz)
    elif period == MONTH: return get_end_of_month(period_start_time, timerange, localtz)


def is_conflicting(range_start, range_end, event_start, event_end):
    """Returns whether or not event times conflict with the provided range."""
    return (range_start <= event_start < range_end or
            range_start < event_end <= range_end or
            (event_start < range_start and event_end > range_end))


def in_timerange(range_start, range_end, event_start, event_end):
    """Returns whether or not event times are contained in provided range."""
    return (range_start <= event_start <= range_end and
            range_start <= event_end <= range_end)


def update_index(index, events, threshold_time):
    """Returns index of first event with end time proceeding the threshold time."""
    while (index < len(events) and
           parse_datetime(events[index]['end']) <= threshold_time):
        index += 1
    return index


def get_range_start_end(timerange, localtz):
    """Returns start and end datetime objects of the timerange provided."""
    range_start = parse_datetime(timerange['start']).astimezone(localtz)
    range_end = parse_datetime(timerange['end']).astimezone(localtz)
    return range_start, range_end
