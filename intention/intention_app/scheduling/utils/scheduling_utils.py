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
get_reschedule_end_time(day, deadline, localtz)
get_minimum_start_times(events, current_time)
get_event_length(event)
get_event_duration(timeunit, duration)
is_conflicting(range_start, range_end, event_start, event_end)
in_timerange(range_start, range_end, event_start, event_end)
get_range_freebusy(timerange, localtz)
get_range_gcal_events(timerange, localtz)
update_index_freebusy(index, freebusy_ranges, threshold_time)
update_index_gcal_events(index, gcal_events, threshold_time)
update_index_rescheduled(index, rescheduled_events, threshold_time)
"""

from intention_app.scheduling.utils.datetime_utils import *

# Length scheduled when period is months.
NUMBER_MONTHS_TO_SCHEDULE = 3

# Rescheduling options.
TODAY = "TODAY"
THIS_WEEK = "THIS_WEEK"
NEXT_WEEK = "NEXT_WEEK"


def unpack_form(form_data):
    """Returns each field required for scheduling in the django form."""
    name = form_data['name']
    frequency = int(form_data['frequency'])
    period = form_data['period']
    duration = int(form_data['duration'])
    timeunit = form_data['timeunit']
    timerange = form_data['timerange']
    return name, frequency, period, duration, timeunit, timerange


def get_start_time(curr_time, timerange, day_start_time, day_end_time):
    """Returns first time available for scheduling within timerange."""
    next_hour = make_next_hour(curr_time)
    range_start, range_end = get_timerange_start_end_time(curr_time, timerange, day_start_time, day_end_time)
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


def get_start_of_next_period(curr_period_start_time, period, timerange, localtz, day_start_time):
    """Returns the first day of the next period set to start hour."""
    if period == DAY: return get_start_of_next_day(curr_period_start_time, timerange, localtz, day_start_time)
    elif period == WEEK: return get_start_of_next_week(curr_period_start_time, timerange, localtz, day_start_time)
    elif period == MONTH: return get_start_of_next_month(curr_period_start_time, timerange, localtz, day_start_time)


def get_start_of_next_event(curr_event_start_time, last_scheduled_event_end_time, period, timerange, localtz,
                            day_start_time):
    """Returns the first day on which the next event can be scheduled set to start hour."""
    if period == DAY: return last_scheduled_event_end_time
    elif period == WEEK: return get_start_of_next_day(curr_event_start_time, timerange, localtz, day_start_time)
    elif period == MONTH: return get_start_of_next_week(curr_event_start_time, timerange, localtz, day_start_time)


def get_end_of_multi_period(day, period, timerange, localtz, day_start_time, day_end_time):
    """Returns the last day of the current multiperiod set to end hour."""
    if period == DAY: return get_end_of_week(day, timerange, localtz, day_start_time, day_end_time)
    elif period == WEEK: return get_end_of_month(day, timerange, localtz, day_start_time, day_end_time)
    elif period == MONTH: return get_end_of_quarter(day, timerange, localtz, day_start_time, day_end_time)


def get_end_of_period(period_start_time, period, timerange, localtz, day_start_time, day_end_time):
    """Returns the last day of the current period set to end hour."""
    if period == DAY: return get_end_of_day(period_start_time, timerange, day_start_time, day_end_time)
    elif period == WEEK: return get_end_of_week(period_start_time, timerange, localtz, day_start_time, day_end_time)
    elif period == MONTH: return get_end_of_month(period_start_time, timerange, localtz, day_start_time, day_end_time)


def get_reschedule_start_time(day, deadline, localtz, day_start_time, day_end_time):
    """Returns the start time for the deadline provided, relative to the current time."""
    if (day_end_time <= day.time() < day_start_time or
        day.time() < day_start_time < day_end_time or
        day_start_time < day_end_time <= day.time()):
        day = get_start_of_next_day(day, "ANYTIME", localtz, day_start_time)
    if deadline == TODAY: return make_next_hour(day)
    elif deadline == THIS_WEEK: return get_start_of_next_day(day, "ANYTIME", localtz, day_start_time)
    elif deadline == NEXT_WEEK: return get_start_of_next_week(day, "ANYTIME", localtz, day_start_time)


def get_reschedule_end_time(day, deadline, localtz, day_start_time, day_end_time):
    """Returns the end time for the deadline provided, relative to the current time."""
    if deadline == TODAY: return make_day_end(day, day_start_time, day_end_time)
    elif deadline == THIS_WEEK: return get_end_of_week(day, "ANYTIME", localtz, day_start_time, day_end_time)
    elif deadline == NEXT_WEEK: return get_end_of_week(get_next_week(day, localtz), "ANYTIME", localtz, day_start_time,
                                                       day_end_time)


def get_minimum_start_times(events, reschedule_start_time):
    """Returns list of provided events along with their minimum start time.

    Minimum start time is defined as later the max of the hour proceeding
    the current time and the hour proceeding the existing start time of an event.
    """
    events_with_min_times = []
    for event in events:
        event_end_time = parse_datetime(event['end']['dateTime'])
        if not is_whole_hour(event_end_time):
            event_end_time = make_next_hour(event_end_time)
        min_start_time = max(reschedule_start_time, event_end_time)
        events_with_min_times.append((event, min_start_time))
    return events_with_min_times


def get_event_length(event):
    """Returns the length of an event based on its start and end datetimes."""
    event_original_start_time = parse_datetime(event["start"]["dateTime"])
    event_original_end_time = parse_datetime(event["end"]["dateTime"])
    return event_original_end_time - event_original_start_time


def get_event_duration(timeunit, duration):
    """Returns the length of an event based on its timeunit and duration."""
    if timeunit == HOURS: return timedelta(hours=duration)
    elif timeunit == MINUTES: return timedelta(minutes=duration)


def is_conflicting(range_start, range_end, event_start, event_end):
    """Returns whether or not event times conflict with the provided range."""
    return (range_start <= event_start < range_end or
            range_start < event_end <= range_end or
            (event_start < range_start and event_end > range_end))


def in_timerange(range_start, range_end, event_start, event_end):
    """Returns whether or not event times are contained in provided range."""
    return (range_start <= event_start <= range_end and
            range_start <= event_end <= range_end)


def get_range_freebusy(index, freebusy_ranges, localtz):
    """Returns start and end datetime objects of the event list at index provided.

    Expects list of google calendar freebusy time ranges.
    """
    if index < len(freebusy_ranges):
        range_start = parse_datetime(freebusy_ranges[index]['start']).astimezone(localtz)
        range_end = parse_datetime(freebusy_ranges[index]['end']).astimezone(localtz)
        return range_start, range_end
    else:
        return None, None


def get_range_gcal_events(index, gcal_events, localtz):
    """Returns start and end datetime objects of the event list at index provided.

    Expects list of google calendar events in event resource representation.
    """
    if index < len(gcal_events):
        range_start = parse_datetime(gcal_events[index]['start']['dateTime']).astimezone(localtz)
        range_end = parse_datetime(gcal_events[index]['end']['dateTime']).astimezone(localtz)
        return range_start, range_end
    else:
        return None, None


def get_range_rescheduled(index, rescheduled_events):
    """Returns start and end datetime objects of the event list at index provided.

    Expects list of rescheduled events in format (event_object, new_start_time, new_end_time)
    """
    if index < len(rescheduled_events):
        range_start = rescheduled_events[index][1]
        range_end = rescheduled_events[index][2]
        return range_start, range_end
    else:
        return None, None


def update_index_freebusy(index, freebusy_ranges, threshold_time):
    """Returns index of first event with end time proceeding the threshold time.

    Expects list of google calendar freebusy time ranges.
    """
    while index < len(freebusy_ranges) and parse_datetime(freebusy_ranges[index]['end']) <= threshold_time:
        index += 1
    return index


def update_index_gcal_events(index, gcal_events, threshold_time):
    """Returns index of first event with end time proceeding the threshold time.

    Expects list of google calendar events in event resource representation.
    """
    while index < len(gcal_events) and parse_datetime(gcal_events[index]['end']['dateTime']) <= threshold_time:
        index += 1
    return index


def update_index_rescheduled(index, rescheduled_events, threshold_time):
    """Returns index of first event with end time proceeding the threshold time.

    Expects list of rescheduled events in format (event_object, new_start_time, new_end_time)
    """
    while index < len(rescheduled_events) and rescheduled_events[index][2] <= threshold_time:
        index += 1
    return index
