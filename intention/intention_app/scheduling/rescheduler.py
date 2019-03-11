"""Module to intelligently reschedule user events.

Reschedules a provided list of events by a deadline and communicates
these updates to the Google Calendar API to reflect in the user cal.

Exported Functions
------------------
reschedule(events, deadline, credentials)
get_events_current_day(credentials)
"""

from __future__ import print_function
from datetime import datetime, timedelta
from intention_app.scheduling.utils.googleapi_utils import *
from intention_app.scheduling.utils.scheduling_utils import *

TODAY = "TODAY"
LATER_THIS_WEEK = "LATER_THIS_WEEK"
NEXT_WEEK = "NEXT_WEEK"


def reschedule(events, deadline, credentials):
    """Reschedules events and updates user calendar with new event times.

    If there's no time left in the day for some events, notify the user.
    """
    rescheduled_events = _reschedule_events(events, deadline, credentials)
    if not rescheduled_events: return False
    update_events_in_calendar(credentials, rescheduled_events)
    return True


def _reschedule_events(events, deadline, credentials):
    """Reschedules provided list of events by the deadline provided.

    Events with start times before the current time must be scheduled
    later than the current time. Events with start times after the
    current time must be scheduled after their original start time.
    """
    localtz = get_localtz(credentials)
    events_with_times = get_minimum_start_times(events, localtz)
    scheduling_deadline = get_scheduling_deadline(deadline, localtz)
    for event, start_time in events_with_times:
        if start_time > scheduling_deadline: return None  # edge case (ie event_start=12:30am, endTime=12:00am)
    busy_times = get_busy_times(credentials, events_with_times, scheduling_deadline, localtz)
    return _reschedule_multiple_events(events_with_times, scheduling_deadline, busy_times, localtz)


def get_minimum_start_times(events, localtz):
    events_with_min_times = []
    current_time = datetime.now(localtz)
    for event in events:
        event_start_time = parse_datetime(event['start']['dateTime'])
        later_time = max(current_time, event_start_time)
        min_start_time = make_next_hour(later_time)
        events_with_min_times.append((event, min_start_time))
    return events_with_min_times


def get_scheduling_deadline(deadline, localtz):
    now = datetime.now(localtz)
    if deadline == TODAY: return make_day_end(now)
    elif deadline == LATER_THIS_WEEK: return get_end_of_week(now, "ANYTIME", localtz)
    elif deadline == NEXT_WEEK: pass


def get_busy_times(credentials, events_with_times, scheduling_deadline, localtz):
    _, event_map = get_events_in_range(credentials, make_next_hour(datetime.now(localtz)), scheduling_deadline)
    busy_times_all = sorted(event_map.values(), key=lambda x: x['start']['dateTime'])
    event_ids = [event['id'] for event, time in events_with_times]
    busy_times = [event for event in busy_times_all if event['id'] not in event_ids]
    return busy_times


def _reschedule_multiple_events(events, deadline, busy_times, localtz):
    range_start = make_day_start(datetime.now(localtz))
    range_end = make_day_end(datetime.now(localtz))
    rescheduled_events = []
    for event, event_start in events:
        event_length = get_event_length(event)
        max_start_time = deadline - event_length
        busy_index = update_index_events(0, busy_times, event_start)
        success, start_time, end_time = _reschedule_single_event(event_start, event_length, max_start_time, rescheduled_events,
                                                                 localtz, range_start, range_end, busy_times,
                                                                 busy_index)
        if not success: return None
        rescheduled_events.append((event, start_time, end_time))
        range_start = make_day_start(datetime.now(localtz))
        range_end = make_day_end(datetime.now(localtz))

    for event, new_start, new_end in rescheduled_events:
        event['start']['dateTime'] = new_start.isoformat()
        event['end']['dateTime'] = new_end.isoformat()
    return [event for event, new_start, new_end in rescheduled_events]


def _reschedule_single_event(event_start, event_length, max_start_time, new_events, localtz,
                             range_start, range_end, busy_times, busy_index):
    event_end = event_start + event_length
    while busy_index < len(busy_times) and event_start <= max_start_time:
        busy_start, busy_end = get_range_start_end_events(busy_times[busy_index], localtz)
        conflicting_index = _conflicts_new_events(new_events, event_start, event_start)
        if not in_timerange(range_start, range_end, event_start, event_end):
            range_start, range_end, event_start, busy_index = update_range(range_start, range_end, event_start,
                                                                           busy_index, busy_times)
        elif is_conflicting(busy_start, busy_end, event_start, event_end):
            event_start = busy_end
            busy_index += 1
            if not in_timerange(range_start, range_end, event_start, event_start + event_length):
                range_start, range_end, event_start, busy_index = update_range(range_start, range_end, event_start,
                                                                               busy_index, busy_times)
        elif conflicting_index != -1:
            event_start = new_events[conflicting_index][2]
            busy_index = update_index_events(busy_index, busy_times, range_start)
            if not in_timerange(range_start, range_end, event_start, event_start + event_length):
                range_start, range_end, event_start, busy_index = update_range(range_start, range_end, event_start,
                                                                               busy_index, busy_times)
        else:
            break
        event_end = event_start + event_length
    search_successful = event_start <= max_start_time
    return search_successful, event_start, event_end


def update_range(range_start, range_end, event_start, busy_index, busy_times):
    range_start += timedelta(days=1)
    range_end += timedelta(days=1)
    event_start = range_start
    busy_index = update_index_events(busy_index, busy_times, range_start)
    return range_start, range_end, event_start, busy_index


def _conflicts_new_events(new_events, event_start, event_end):
    for i in range(len(new_events)):
        event = new_events[i]
        new_start = event[1]
        new_end = event[2]
        if is_conflicting(new_start, new_end, event_start, event_end):
            return i
    return -1


def get_events_current_day(credentials):
    localtz = get_localtz(credentials)
    current_day = datetime.now(localtz)
    day_start = make_day_start(current_day)
    day_end = make_day_end(current_day)
    ids_and_titles, event_map = get_events_in_range(credentials, day_start, day_end)
    return ids_and_titles, event_map
