"""Module to intelligently reschedule user events."""

from __future__ import print_function
from datetime import datetime
from intention_app.scheduling.utils.googleapi_utils import get_service, get_localtz, get_events_from_calendar

def get_tasks(): 
    service = get_service()
    localtz = get_localtz(service)
    time_min = datetime.now(localtz)
    time_max = datetime.now(localtz)
    tasks =  get_events_from_calendar(service, time_min, time_max)
    print('### returned tasks ###')
    print(tasks)
    return tasks

# All selected events should be rescheduled for a later time
# in the day than they are currently scheduled for.
#
# Events whose start times are before the current time have the
# added constraint that they need to be later than the current time.
#
# If there's no time left in the day for some events, notify the user.
def reschedule(form_data):
    service = get_service()
    # TODO: implement this
    return True


