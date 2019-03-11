"""Module to intelligently reschedule user events."""

from __future__ import print_function
from datetime import datetime, timedelta
from intention_app.scheduling.utils.googleapi_utils import *
from intention_app.scheduling.utils.scheduling_utils import *


def reschedule(events, credentials):
    """All selected events should be rescheduled for a later time
    in the day than they are currently scheduled for.

    Events whose start times are before the current time have the
    added constraint that they need to be later than the current time.

    If there's no time left in the day for some events, notify the user."""
    localtz = get_localtz(credentials)
    current_day = datetime.now(localtz)
    day_start = make_day_start(current_day)
    day_end = make_day_end(current_day)
    day_events = get_events_in_day(credentials, day_start, day_end)
    return True


def _reschedule_multiple_events(rescheduled_events, endtime, busy_times, localtz):
    """Reschedules all events to before endtime, or says which events can't be rescheduled before endtime."""
    range_start = make_day_start(datetime.now(localtz))
    range_end = make_day_end(datetime.now(localtz))
    new_events = [] # stores tuple (start_time, end_time) on per-event basis
    for event in rescheduled_events:
        event_start = event[1]
        if event_start > endtime: return None # edge case (something like event_start=12:30am, endTime=12:00am)
        event_original_start_time = parse_datetime(event["start"]["dateTime"])
        event_original_end_time = parse_datetime(event["end"]["dateTime"])
        event_length = event_original_end_time - event_original_start_time
        max_start_time = endtime - event_length
        success, start_time, end_time = _reschedule_single_event(busy_times, range_start, range_end, event_start,
                                                                 max_start_time, 0, localtz, new_events, event_length)
        new_events.append((event, start_time, end_time))
        range_start = make_day_start(datetime.now(localtz))
        range_end = make_day_end(datetime.now(localtz))
    # create event api calls for new events
    return True

def _reschedule_single_event(busy_times, range_start, range_end, event_start, max_start_time, busy_range_index, localtz,
                             new_events, event_length):
    event_end = event_start + event_length
    busy_start, busy_end = get_range_start_end(busy_times[busy_range_index], localtz)
    while (busy_range_index < len(busy_times) and event_start <= max_start_time and
           (is_conflicting(busy_start, busy_end, event_start, event_end) or
           conflicts_new_events(new_events, event_start, event_end))):
        if event_end > range_end:
            range_start += timedelta(days=1)
            range_end += timedelta(days=1)
            event_start = range_start
            busy_range_index = update_index(busy_range_index, busy_times, range_start)
        else:
            if is_conflicting(busy_start, busy_end, event_start, event_end):
                event_start = busy_end
                busy_range_index += 1
            # else:
        event_end = increment_time(event_start, timeunit, duration)
        if busy_range_index < len(busy_times):
            busy_start, busy_end = get_range_start_end(busy_times[busy_range_index], localtz)
    search_successful = event_start <= max_start_time and in_timerange(range_start, range_end, event_start, event_end)
    return search_successful, event_start, event_end


def conflicts_new_events(new_events, event_start, event_end):
    for event in new_events:
        new_start = event[1]
        new_end = event[2]
        if is_conflicting(new_start, new_end, event_start, event_end):
            return True
    return False


def get_events_current_day(credentials):
    localtz = get_localtz(credentials)
    current_day = datetime.now(localtz)
    day_start = make_day_start(current_day)
    day_end = make_day_end(current_day)
    ids_and_titles, event_map = get_events_in_range(credentials, day_start, day_end)
    return ids_and_titles, event_map
