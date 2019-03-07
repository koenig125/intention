"""Module to intelligently reschedule user events."""

from __future__ import print_function
from datetime import datetime, timedelta
from intention_app.scheduling.utils.datetime_utils import make_day_start, make_day_end
from intention_app.scheduling.utils.googleapi_utils import get_localtz, get_events_in_range


# All selected events should be rescheduled for a later time
# in the day than they are currently scheduled for.
#
# Events whose start times are before the current time have the
# added constraint that they need to be later than the current time.
#
# If there's no time left in the day for some events, notify the user.
def reschedule(form_data, service):
    # TODO: implement this
    return True


def get_events_current_day(service):
    localtz = get_localtz(service)
    current_day = datetime.now(localtz)
    day_start = make_day_start(current_day)
    day_end = make_day_end(current_day)
    events =  get_events_in_range(service, day_start, day_end)
    print('### returned tasks ###')
    print(events)
    return events
