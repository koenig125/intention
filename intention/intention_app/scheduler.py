"""A module that intelligently schedules new events.

Scheduler.py retrieves a user's Google Calendar via the Google
Oauth process and uses this calendar to determine when to schedule
new events on behalf of the user. The only function exported by
this module is make_schedule - all other functions are private.
"""

from __future__ import print_function
from .schedule_utils import *
from datetime import datetime


def make_schedule(form_data):
    service = get_credentials()
    events = schedule_events(form_data, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True


def schedule_events(form_data, service):
    events = schedule_events_using_consolidated_periods(form_data, service)
    if not events: events = schedule_events_for_multiple_periods(form_data, service)
    return events


def schedule_events_using_consolidated_periods(form_data, service):
    """Coordinates event scheduling over multiple consolidated time periods.

    This function consolidates a user's schedule for multiple periods
    into a single period so that times that are free in every period
    can be easily identified. This provides consistency in scheduling.

    :param form_data: Data from user detailing when and what to schedule.
    :param service: Object through which Google API calls are made.
    :return: List of events in json format to add to user calendar.
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    localtz = get_local_timezone(service)
    period_start_time = make_start_time(get_next_week(datetime.now(localtz), localtz), timerange)
    period_end_time = get_period_end_time(period, timerange, period_start_time, localtz)
    if period_start_time > period_end_time: return None
    multi_period_end_time = get_multi_period_end_time(period, timerange, period_start_time, localtz)
    event_start_time = period_start_time
    event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    range_start, range_end = get_desired_time_range(period_start_time, timerange)
    busy_times = get_busy_times(service, period_start_time, multi_period_end_time)
    consolidated = consolidate_busy_times(period, period_start_time, period_end_time, localtz, busy_times)
    events = schedule_events_for_single_period(form_data, event_start_time, event_start_time_max,
                                               consolidated, range_start, range_end, localtz)
    if not events: return None
    return copy_events_for_each_period(events, period, period_start_time, name, localtz)


def schedule_events_for_multiple_periods(form_data, service):
    """Coordinates event scheduling over multiple periods of time.

    This function coordinates scheduling efforts over multiple periods. If period
    is day, schedules events daily until the end of the week. If week, schedules
    events weekly until the 2nd to last week of the current month. If month,
    schedules events monthly for the current month and 2 months further.

    :param form_data: Data from user detailing when and what to schedule.
    :param service: Object through which Google API calls are made.
    :return: List of all events to add to user calendar, in json format.
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    localtz = get_local_timezone(service)
    period_start_time = make_start_time(get_next_week(datetime.now(localtz), localtz), timerange)
    period_end_time = get_period_end_time(period, timerange, period_start_time, localtz)
    # period_start_time = get_first_available_time(datetime.now(localtz), timerange)
    # period_end_time = get_period_end_time(period, timerange, datetime.now(localtz), localtz)
    if period_start_time > period_end_time: return None # Triggered when can't schedule event by end of current day/week
    event_start_time = period_start_time
    event_start_time_max = decrement_time(period_end_time, timeunit, duration)
    busy_times = get_busy_times(service, period_start_time, period_end_time)
    range_start, range_end = get_desired_time_range(period_start_time, timerange)
    num_periods = get_number_periods(period, period_start_time, localtz)

    events = []
    for i in range(num_periods):
        events_for_single_period = schedule_events_for_single_period(form_data, event_start_time, event_start_time_max,
                                                                     busy_times, range_start, range_end, localtz)
        if not events_for_single_period: return None
        else: events.extend(events_for_single_period)
        period_start_time = get_next_period_start_time(period, timerange, period_start_time, localtz)
        period_end_time = get_period_end_time(period, timerange, period_start_time, localtz)
        event_start_time = period_start_time
        event_start_time_max = decrement_time(period_end_time, timeunit, duration)
        busy_times = get_busy_times(service, period_start_time, period_end_time)
        range_start, range_end = get_desired_time_range(period_start_time, timerange)
    return events


def schedule_events_for_single_period(form_data, event_start_time, event_start_time_max, busy_times, range_start,
                                      range_end, localtz):
    """Coordinates event scheduling over single period of time.

    This function schedules a set number of events in a single period of time,
    as determined by the frequency parameter provided by the user in form_data.

    :param form_data: Data from user detailing when and what to schedule.
    :param event_start_time: Start time of new event to be scheduled.
    :param event_start_time_max: Last possible start time an event could be
    scheduled in the period between period_start_time and period_end_time.
    :param busy_times: List of busy chunks of time in user's schedule.
    :param range_start: Start time in day in which events can be scheduled.
    :param range_end: End time in day in which events can be scheduled.
    :param localtz: Object representing the local timezone of the user.
    :return: List of events for single period to add to user calendar, in json format.
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form_data)
    event_index = 0
    events = []
    for i in range(frequency):
        if event_start_time > event_start_time_max: return None
        success, start_time, end_time = find_time_for_single_event(busy_times, duration, timeunit, range_start,
                                                                   range_end, event_start_time, event_start_time_max,
                                                                   event_index, localtz)
        if not success: return None
        events.append(create_event(name, start_time, end_time))
        event_start_time = get_next_event_start_time(period, timerange, start_time, end_time, localtz)
        if period != DAY: range_start, range_end = get_desired_time_range(event_start_time, timerange)
        event_index = update_event_index(busy_times, event_start_time, event_index)
    return events


def find_time_for_single_event(busy_times, duration, timeunit, range_start, range_end, event_start, max_start_time,
                               event_index, localtz):
    """Searches a user's calendar for free time to create new event.

    This function is directly responsible for finding the time bounds
    in which an event is to be scheduled within the range (morning,
    afternoon, night, or anytime) specified by the user.

    :param busy_times: List of chunks of times on user's calendar that have existing events.
    :param duration: Length of the event as specified by user.
    :param timeunit: Hours or minutes unit, specified by user.
    :param range_start: Start time in day in which events can be scheduled.
    :param range_end: End time in day in which events can be scheduled.
    :param event_start: Proposed start time of event.
    :param max_start_time: Last possible start time an event could be
    scheduled in the period between period_start_time and period_end_time.
    :param event_index: Index to track location in busy_times listing.
    :param localtz: Object representing the local timezone of the user.
    :return: Flag for whether or not time was found, along with the start
    and end time of the new event to be added to the user calendar if so.
    """
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
