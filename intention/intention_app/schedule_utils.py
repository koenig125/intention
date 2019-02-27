from __future__ import print_function
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from calendar import monthrange

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server()
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return service

def get_local_timezone(service):
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone_name = calendar['timeZone']
    return timezone(timezone_name)
