"""Module to intelligently schedule new events on behalf of ther user.

Retrieves a user's Google Calendar via the Google Oauth process and uses
this cal to determine when to schedule new events on behalf of the user.

Exported Functions
------------------
schedule(form_data)
"""

from __future__ import print_function
from intention_app.scheduling.consolidator import consolidate_multiple_periods
from intention_app.scheduling.utils.googleapi_utils import *
from intention_app.scheduling.utils.scheduling_utils import *
from datetime import datetime


def schedule(form, preferences, credentials):
    """Schedules events based on form_data and adds them to user Google calendar.

    Returns whether or not events were successfully scheduled based on availability.
    """
    events = _schedule_events(form, preferences, credentials)
    if not events: return False
    add_events_to_calendar(credentials, events, preferences.calendar_id)
    return True


def _schedule_events(form, preferences, credentials):
    """Returns events to add to user calendar for multiple consecutive time periods.

    If period is day, schedules events daily until the end of the week. If week,
    schedules events weekly until the 2nd to last week of the current month. If
    month, schedules events monthly for the current month and 2 months further.
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    day_start_time = preferences.day_start_time
    day_end_time = preferences.day_end_time
    calendar_id = preferences.calendar_id
    localtz = get_localtz(credentials, calendar_id)

    period_start_time = get_start_time(datetime.now(localtz), timerange, day_start_time, day_end_time)
    period_end_time = get_end_of_period(datetime.now(localtz), period, timerange, localtz, day_start_time, day_end_time)
    if period_start_time > period_end_time: return None # Can't schedule event by end of day/week
    day_start, day_end = get_timerange_start_end_time(period_start_time, timerange, day_start_time, day_end_time)
    event_start = period_start_time
    event_length = get_event_duration(timeunit, duration)
    event_start_max = period_end_time - event_length

    events_consolidated = _schedule_events_consolidated_periods(form, preferences, credentials, localtz, period_start_time,
                                                                period_end_time, day_start, day_end, event_start,
                                                                event_length, event_start_max)
    if events_consolidated: return events_consolidated
    events_multiple = _schedule_events_multiple_periods(form, preferences, credentials, localtz, period_start_time, period_end_time,
                                                        day_start, day_end, event_start, event_length, event_start_max)
    return events_multiple


def _schedule_events_consolidated_periods(form, preferences, credentials, localtz, first_period_start, first_period_end,
                                          day_start, day_end, event_start, event_length, event_start_max):
    """Returns events to add to user calendar using consolidated time periods.

    Consolidates user calendar free busy information across multiple periods into a
    single period timeframe and attempts to schedule events within that timeframe.
    :param event_length:
    """
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    day_start_time = preferences.day_start_time
    day_end_time = preferences.day_end_time
    calendar_id = preferences.calendar_id

    multi_period_end = get_end_of_multi_period(first_period_start, period, timerange, localtz, day_start_time,
                                               day_end_time)
    freebusy_ranges = get_freebusy_in_range(credentials, first_period_start, multi_period_end, calendar_id)
    consolidated = consolidate_multiple_periods(freebusy_ranges, first_period_start, first_period_end, period, localtz)
    events = _schedule_events_single_period(form, preferences, localtz, day_start, day_end, event_start, event_length,
                                            event_start_max, consolidated)
    if not events: return None
    num_copies = get_number_periods(first_period_start, period, localtz) - 1
    return _copy_events(events, num_copies, period, name, localtz)


def _schedule_events_multiple_periods(form, preferences, credentials, localtz, period_start_time, period_end_time,
                                      day_start, day_end, event_start, event_length, event_start_max):
    """Returns events to add to user calendar for multiple consecutive time periods.

    Does not consolidate user calendar free busy information. Rather, schedules across
    multiple time periods directly, provides more flexibility, but less consistency.
    :param event_length:
    """
    events = []
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    day_start_time = preferences.day_start_time
    day_end_time = preferences.day_end_time
    calendar_id = preferences.calendar_id

    freebusy_ranges = get_freebusy_in_range(credentials, period_start_time, period_end_time, calendar_id)
    num_periods = get_number_periods(period_start_time, period, localtz)
    for i in range(num_periods):
        events_for_single_period = _schedule_events_single_period(form, preferences, localtz, day_start, day_end,
                                                                  event_start, event_length, event_start_max, freebusy_ranges)
        if not events_for_single_period: return None
        else: events.extend(events_for_single_period)
        period_start_time = get_start_of_next_period(period_start_time, period, timerange, localtz, day_start_time)
        period_end_time = get_end_of_period(period_start_time, period, timerange, localtz, day_start_time, day_end_time)
        event_start = period_start_time
        event_start_max = period_end_time - event_length
        day_start, day_end = get_timerange_start_end_time(period_start_time, timerange, day_start_time, day_end_time)
        freebusy_ranges = get_freebusy_in_range(credentials, period_start_time, period_end_time, calendar_id)
    return events


def _schedule_events_single_period(form, preferences, localtz, day_start, day_end, event_start, event_length,
                                   event_start_max, freebusy_ranges):
    """Returns events to add to user calendar for single period of time.
    :param event_length:
    """
    events = []
    freebusy_index = 0
    name, frequency, period, duration, timeunit, timerange = unpack_form(form)
    day_start_time = preferences.day_start_time
    day_end_time = preferences.day_end_time
    calendar_id = preferences.calendar_id

    for i in range(frequency):
        if event_start > event_start_max: return None
        success, start_time = _find_time_for_single_event(localtz, day_start, day_end, event_start, event_length,
                                                          event_start_max, freebusy_ranges, freebusy_index)
        if not success: return None
        events.append(create_event(name, start_time, start_time + event_length))
        event_start = get_start_of_next_event(start_time, start_time + event_length, period, timerange, localtz, day_start_time)
        if period != DAY: day_start, day_end = get_timerange_start_end_time(event_start, timerange, day_start_time, day_end_time)
        freebusy_index = update_index_freebusy(freebusy_index, freebusy_ranges, event_start)
    return events


def _find_time_for_single_event(localtz, day_start, day_end, event_start, event_length, max_start_time,
                                freebusy_ranges, freebusy_index):
    """Returns start and end bounds for single event within timerange provided."""
    while freebusy_index < len(freebusy_ranges) and event_start <= max_start_time:
        event_end = event_start + event_length
        freebusy_index = update_index_freebusy(freebusy_index, freebusy_ranges, event_start)
        busy_start, busy_end = get_range_freebusy(freebusy_index, freebusy_ranges, localtz)

        # Conflicts with existing event on calendar.
        if busy_start and is_conflicting(busy_start, busy_end, event_start, event_end):
            event_start = busy_end

        # If not conflicting above, and in desired timerange, success.
        elif in_timerange(day_start, day_end, event_start, event_end):
            break

        # Check if updated start time is outside the desired timerange.
        if not in_timerange(day_start, day_end, event_start, event_end):
            day_start += timedelta(days=1)
            day_end += timedelta(days=1)
            event_start = day_start

    search_successful = event_start <= max_start_time
    return search_successful, event_start


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
