"""Module to intelligently reschedule user events.

Reschedules a provided list of events by a deadline and communicates
these updates to the Google Calendar API to reflect in the user cal.

Exported Functions
------------------
reschedule(events, deadline, preferences, credentials)
get_events_current_day(credentials, preferences)
"""

from __future__ import print_function

from datetime import datetime

from intention_app.scheduling.utils.googleapi_utils import *
from intention_app.scheduling.utils.scheduling_utils import *


def reschedule(events, deadline, preferences, credentials):
    """Reschedules events and updates user calendar with new event times."""
    rescheduled_events = _reschedule_events(events, deadline, preferences, credentials)
    if not rescheduled_events: return False, None
    cid = update_events_in_calendar(credentials, rescheduled_events)
    return True, cid


def get_events_current_day(credentials, preferences):
    """Returns events from DAY_START_HOUR to DAY_END_HOUR for user indicated in credentials."""
    day_start_time, day_end_time, calendar_id, calendars = unpack_preferences(preferences)
    localtz = get_localtz(credentials, calendar_id)
    current_day = datetime.now(localtz)
    events = get_events_in_range(credentials, make_day_start(current_day, day_start_time),
                                 make_day_end(current_day, day_start_time, day_end_time), calendars)
    return _filter_event_information(events)


def _reschedule_events(events, deadline, preferences, credentials):
    """Reschedules provided list of events by the deadline provided.

    Events with start times before the current time must be scheduled
    later than the current time. Events with start times after the
    current time must be scheduled after their original start time.
    """
    day_start_time, day_end_time, calendar_id, calendars = unpack_preferences(preferences)
    localtz = get_localtz(credentials, calendar_id)
    now = datetime.now(localtz)

    reschedule_start = get_reschedule_start_time(now, deadline, localtz, day_start_time)
    reschedule_end = get_reschedule_end_time(now, deadline, localtz, day_start_time, day_end_time)
    if reschedule_start > reschedule_end:
        # edge case - current time past day_end_time and rescheduled later today
        return None
    events_with_min_times = get_minimum_start_times(events, reschedule_start)
    for event, start_time in events_with_min_times:
        # edge case (ie start_time=12:30am, deadline=12:00am)
        if start_time > reschedule_end: return None
    event_ids = [event['id'] for event in events]
    existing_events = get_events_in_range(credentials, reschedule_start, reschedule_end, calendars)
    filtered_events = [event for event in existing_events if event['id'] not in event_ids]
    return _reschedule_multiple_events(events_with_min_times, reschedule_end, preferences, filtered_events, localtz)


def _reschedule_multiple_events(events, deadline, preferences, existing_events, localtz):
    """Finds new times to rschedule multiple events by provided deadline."""
    day_start_time, day_end_time, calendar_id, calendars = unpack_preferences(preferences)
    rescheduled_events = []
    for event, event_start in events:
        event_length = get_event_length(event)
        max_start_time = deadline - event_length
        range_start, range_end = get_day_start_end_time(event_start, day_start_time, day_end_time)
        existing_event_index = update_index_gcal_events(0, existing_events, event_start)
        rescheduled_event_index = update_index_rescheduled(0, rescheduled_events, event_start)
        success, start_time = _reschedule_single_event(event_start, event_length, max_start_time, range_start,
                                                       range_end, localtz, existing_events, existing_event_index,
                                                       rescheduled_events, rescheduled_event_index)
        if not success: return None
        rescheduled_events.append((event, start_time, start_time + event_length))
    return _replace_event_times(rescheduled_events)


def _reschedule_single_event(event_start, event_length, max_start_time, range_start, range_end, localtz,
                             existing_events, existing_index, resched_events, resched_index):
    """Finds new time to reschedule single event by max_start_time deadline."""
    while event_start <= max_start_time and (existing_index < len(existing_events) or
                                             resched_index < len(resched_events)):
        event_end = event_start + event_length
        existing_index = update_index_gcal_events(existing_index, existing_events, event_start)
        resched_index = update_index_rescheduled(resched_index, resched_events, event_start)
        existing_start, existing_end = get_range_gcal_events(existing_index, existing_events, localtz)
        resched_start, resched_end = get_range_rescheduled(resched_index, resched_events)

        # Conflicts with existing event on calendar.
        if existing_start and is_conflicting(existing_start, existing_end, event_start, event_end):
            event_start = existing_end

        # Conflicts with another rescheduled event.
        elif resched_start and is_conflicting(resched_start, resched_end, event_start, event_end):
            event_start = resched_end

        # If not conflicting above, and in desired timerange, success.
        elif in_timerange(range_start, range_end, event_start, event_end):
            break

        # Check if updated start time is outside the desired timerange.
        if not in_timerange(range_start, range_end, event_start, event_end):
            range_start += timedelta(days=1)
            range_end += timedelta(days=1)
            event_start = range_start

    search_successful = event_start <= max_start_time
    return search_successful, event_start


def _replace_event_times(rescheduled_events):
    """Returns list of events in rescheduled_events with their start and end times updated."""
    for event, new_start, new_end in rescheduled_events:
        event['start']['dateTime'] = new_start.isoformat()
        event['end']['dateTime'] = new_end.isoformat()
    return [event for event, new_start, new_end in rescheduled_events]


def _filter_event_information(events):
    """Returns ids, titles, and map of event ids to events for list of events provided."""
    ids_and_titles = []
    event_map = {}
    for event in events:
        ids_and_titles.append((event['id'], event['summary']))
        event_map[event['id']] = event
    return ids_and_titles, event_map
