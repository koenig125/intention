from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange

# Authentication information
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Basic time constants
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# Arbitrary limit on the number of months scheduled when period is months.
MONTHS_TO_SCHEDULE = 3

# Bounding hours between which events can be scheduled each day
DAY_START_TIME = 8
DAY_END_TIME = 1

# Periods, timeunits, & timeranges
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"
HOURS, MINUTES = "HOURS", "MINUTES"
MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"

# Timerange hours
MORNING_HOURS = {'start': DAY_START_TIME, 'end': 12}
AFTERNOON_HOURS = {'start': 12, 'end': 18}
EVENING_HOURS = {'start': 18, 'end': DAY_END_TIME}


def reschedule(form_data):
    service = get_credentials()
    events = schedule_events_for_multiple_periods(form_data, service)
    if not events: return False
    add_events_to_calendar(service, events)
    return True


def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service


