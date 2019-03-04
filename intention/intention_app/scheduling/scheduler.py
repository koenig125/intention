"""Module to intelligently schedule new events on behalf of ther user.

Retrieves a user's Google Calendar via the Google Oauth process and uses
this cal to determine when to schedule new events on behalf of the user.

Exported Functions
------------------
make_schedule(form_data)
"""

from __future__ import print_function
from datetime import datetime
from intention_app.scheduling.consolidator import consolidate_multiple_periods
from intention_app.scheduling.utils.googleapi_utils import *
from intention_app.scheduling.utils.scheduling_utils import *


def make_schedule(form):
    """Schedules events based on form_data and adds them to user Google calendar.

    Returns whether or not events were successfully scheduled based on availability.
    """
    service = get_service()
    events = _schedule_events(form, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True


def _schedule_events(form, service):
    """Returns events to add to user calendar for multiple consecutive time periods.

    If period is day, schedules events daily until the end of the week. If week,
    schedules events weekly until the 2nd to last week of the current month. If
    month, schedules events monthly for the current month and 2 months further.
    """
    localtz = get_localtz(service)
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    period_start_time = get_start_time(datetime.now(localtz), timerange)
    period_end_time = get_end_of_period(datetime.now(localtz), period, timerange, localtz)
    if period_start_time > period_end_time: return None # Triggered when can't schedule event by end of day/week
    event_start = period_start_time
    event_start_max = decrement_time(period_end_time, timeunit, duration)
    range_start, range_end = get_day_start_end_times(period_start_time, timerange)

    events_consolidated = _schedule_events_consolidated_periods(form, service, localtz, period_start_time,
                                                period_end_time, event_start, event_start_max, range_start, range_end)
    if events_consolidated: return events_consolidated
    events_multiple = _schedule_events_multiple_periods(form, service, localtz, period_start_time, period_end_time,
                                                       event_start, event_start_max, range_start, range_end)
    return events_multiple


def _schedule_events_consolidated_periods(form, service, localtz, first_period_start, first_period_end,
                                          event_start, event_start_max, range_start, range_end):
    """Returns events to add to user calendar using consolidated time periods.

    Consolidates user calendar free busy information across multiple periods into a
    single period timeframe and attempts to schedule events within that timeframe.
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    multi_period_end = get_end_of_multi_period(first_period_start, period, timerange, localtz)
    busy_times = get_busy_ranges(service, first_period_start, multi_period_end)
    consolidated = consolidate_multiple_periods(busy_times, first_period_start, first_period_end, period, localtz)
    events = _schedule_events_single_period(form, event_start, event_start_max,
                                            consolidated, range_start, range_end, localtz)
    if not events: return None
    num_copies = get_number_periods(first_period_start, period, localtz) - 1
    return _copy_events(events, num_copies, period, name, localtz)


def _schedule_events_multiple_periods(form, service, localtz, period_start_time, period_end_time,
                                      event_start, event_start_max, range_start, range_end):
    """Returns events to add to user calendar for multiple consecutive time periods.

    Does not consolidate user calendar free busy information. Rather, schedules across
    multiple time periods directly, provides more flexibility, but less consistency.
    """
    events = []
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    busy_times = get_busy_ranges(service, period_start_time, period_end_time)
    num_periods = get_number_periods(period_start_time, period, localtz)
    for i in range(num_periods):
        events_for_single_period = _schedule_events_single_period(form, event_start, event_start_max,
                                                                  busy_times, range_start, range_end, localtz)
        if not events_for_single_period: return None
        else: events.extend(events_for_single_period)
        period_start_time = get_start_of_next_period(period_start_time, period, timerange, localtz)
        period_end_time = get_end_of_period(period_start_time, period, timerange, localtz)
        event_start = period_start_time
        event_start_max = decrement_time(period_end_time, timeunit, duration)
        range_start, range_end = get_day_start_end_times(period_start_time, timerange)
        busy_times = get_busy_ranges(service, period_start_time, period_end_time)
    return events


def _schedule_events_single_period(form, event_start, event_start_max, busy_times, range_start, range_end, localtz):
    """Returns events to add to user calendar for single period of time."""
    events = []
    event_index = 0
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    for i in range(frequency):
        if event_start > event_start_max: return None
        success, start_time, end_time = _find_time_for_single_event(busy_times, duration, timeunit, range_start,
                                                                    range_end, event_start, event_start_max,
                                                                    event_index, localtz)
        if not success: return None
        events.append(create_event(name, start_time, end_time))
        event_start = get_start_of_next_event(start_time, end_time, period, timerange, localtz)
        if period != DAY: range_start, range_end = get_day_start_end_times(event_start, timerange)
        event_index = update_index(event_index, busy_times, event_start)
    return events


def _find_time_for_single_event(busy_times, duration, timeunit, range_start, range_end, event_start, max_start_time,
                                event_index, localtz):
    """Returns start and end bounds for single event within timerange provided."""
    if event_index >= len(busy_times): # No more busy times, event_start successful.
        return True, event_start, increment_time(event_start, timeunit, duration)
    event_end = increment_time(event_start, timeunit, duration)
    busy_start, busy_end = get_range_start_end(busy_times[event_index], localtz)
    while (event_index < len(busy_times) and event_start <= max_start_time and
           (is_conflicting(busy_start, busy_end, event_start, event_end) or not
           in_timerange(range_start, range_end, event_start, event_end))):
        if event_end > range_end:
            range_start += timedelta(hours=HOURS_IN_DAY)
            range_end += timedelta(hours=HOURS_IN_DAY)
            event_start = range_start
            event_index = update_index(event_index, busy_times, range_start)
        else:
            event_start = busy_end
            event_index += 1
        event_end = increment_time(event_start, timeunit, duration)
        if event_index < len(busy_times): busy_start, busy_end = get_range_start_end(busy_times[event_index], localtz)
    search_successful = event_start <= max_start_time and in_timerange(range_start, range_end, event_start, event_end)
    return search_successful, event_start, event_end


def _copy_events(events, num_copies, period, name, localtz):
    """Returns copies of events from one period for num_copies additional periods."""
    all_events = events.copy()
    for event in events:
        event_start = parse_datetime(event['start']['dateTime']).astimezone(localtz)
        event_end = parse_datetime(event['end']['dateTime']).astimezone(localtz)
        for i in range(1, num_copies + 1):
            delta_to_future_period = get_timedelta_to_future_period(event_start, period, i, localtz)
            range_start = add_timedelta(delta_to_future_period, event_start, localtz)
            range_end = add_timedelta(delta_to_future_period, event_end, localtz)
            all_events.append(create_event(name, range_start, range_end))
    return all_events
