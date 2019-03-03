"""Module to manipulate datetime objects.

Manipulate datetime objects over days, weeks, and months.

Exported Functions
------------------
make_start_hour(day, timerange)
make_end_hour(day, timerange)
make_next_hour(day)
get_start_of_day(day, timerange)
get_start_of_next_day(day, timerange, localtz)
get_start_of_next_week(day, timerange, localtz)
get_start_of_next_month(day, timerange, localtz)
get_end_of_day(day, timerange)
get_end_of_week(day, timerange, localtz)
get_end_of_month(day, timerange, localtz)
get_end_of_quarter(day, timerange, localtz)
get_next_day(day, localtz)
get_next_week(day, localtz)
get_next_month(day, localtz)
get_next_quarter(day, localtz)
get_days_left_in_week(day)
get_days_left_in_month(day)
get_days_left_in_quarter(day)
get_weeks_left_in_month(day, localtz)
increment_time(day, timeunit, duration)
decrement_time(day, timeunit, duration)
"""

from __future__ import print_function
from datetime import timedelta
from pytz import timezone
from calendar import monthrange

# Basic time constants
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# Bounding hours for event scheduling.
DAY_START_HOUR = 8
DAY_END_HOUR = 1

# Length scheduled when period=months.
MONTHS_TO_SCHEDULE = 3

# Time zones
utc = timezone('UTC')

# Time units
HOURS, MINUTES = "HOURS", "MINUTES"

# Time periods
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"

# Time ranges
MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"

# Timerange hours
AFTERNOON_START = 12
EVENING_START = 18
MORNING_HOURS = {'start': DAY_START_HOUR, 'end': AFTERNOON_START}
AFTERNOON_HOURS = {'start': AFTERNOON_START, 'end': EVENING_START}
EVENING_HOURS = {'start': EVENING_START, 'end': DAY_END_HOUR}


def make_start_hour(day, timerange):
    """Sets day to start hour based on timerange."""
    start_hour = DAY_START_HOUR
    if timerange == MORNING: start_hour = MORNING_HOURS['start']
    elif timerange == AFTERNOON: start_hour = AFTERNOON_HOURS['start']
    elif timerange == EVENING: start_hour = EVENING_HOURS['start']
    return day.replace(hour=start_hour, minute=0, second=0, microsecond=0)


def make_end_hour(day, timerange):
    """Sets day to end hour based on timerange."""
    end_hour = DAY_END_HOUR
    if timerange == MORNING: end_hour = MORNING_HOURS['end']
    elif timerange == AFTERNOON: end_hour = AFTERNOON_HOURS['end']
    elif timerange == EVENING: end_hour = EVENING_HOURS['end']
    if end_hour == DAY_END_HOUR and DAY_END_HOUR < DAY_START_HOUR:
        day += timedelta(days=1) # Day end time is past midnight.
    return day.replace(hour=end_hour, minute=0, second=0, microsecond=0)


def make_next_hour(day):
    """Sets day to hour proceeding the current hour."""
    return day.replace(hour=day.hour, minute=0, second=0, microsecond=0) + timedelta(hours=1)


def get_start_of_day(day, timerange):
    """Returns day provided set to start hour."""
    return make_start_hour(day, timerange)


def get_start_of_next_day(day, timerange, localtz):
    """Returns the day after that provided set to start hour."""
    if day.hour < DAY_START_HOUR: # Day is past midnight.
        return make_start_hour(day, timerange)
    else:
        return make_start_hour(get_next_day(day, localtz), timerange)


def get_start_of_next_week(day, timerange, localtz):
    """Returns the Sunday of the next week set to start hour."""
    return make_start_hour(get_next_week(day, localtz), timerange)


def get_start_of_next_month(day, timerange, localtz):
    """Returns the first day of the next month set to start hour."""
    return make_start_hour(get_next_month(day, localtz), timerange)


def get_end_of_day(day, timerange):
    """Returns the day provided set to end hour."""
    return make_end_hour(day, timerange)


def get_end_of_week(day, timerange, localtz):
    """Returns the Saturday of current week set to end hour."""
    last_day_of_week = get_next_week(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_week, timerange)


def get_end_of_month(day, timerange, localtz):
    """Returns the last day of the current month set to end hour."""
    last_day_of_month = get_next_month(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_month, timerange)


def get_end_of_quarter(day, timerange, localtz):
    """Returns the last day of the last month in the current quarter set to end hour."""
    last_day_of_quarter = get_next_quarter(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_quarter, timerange)


def get_next_day(day, localtz):
    """Returns day incremented by 24 hours."""
    return (day.astimezone(utc) + timedelta(days=1)).astimezone(localtz)


def get_next_week(day, localtz):
    """Returns the Sunday of the next week."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_week(day))).astimezone(localtz)


def get_next_month(day, localtz):
    """Returns the first day of the next month."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_month(day))).astimezone(localtz)


def get_next_quarter(day, localtz):
    """Returns the first day of the next quarter."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_quarter(day))).astimezone(localtz)


def get_days_left_in_week(day):
    """Returns number of days left in the current week. Includes inputted day in count."""
    day_index = (day.weekday() + 1) % DAYS_IN_WEEK
    return DAYS_IN_WEEK - day_index


def get_days_left_in_month(day):
    """Returns number of days left in the current month. Includes inputted day in count."""
    days_in_month = get_days_in_month(day.year, day.month)
    return days_in_month - day.day + 1 # 1 for current day


def get_days_left_in_quarter(day):
    """Returns number of days left in the current quarter. Includes inputted day in count."""
    days_left = get_days_left_in_month(day)
    days_left += get_days_in_month(day.year, day.month + 1)
    days_left += get_days_in_month(day.year, day.month + 2)
    return days_left


def get_weeks_left_in_month(day, localtz):
    """Returns number of weeks left in the current month."""
    last_sunday = get_last_sunday_in_month(day, localtz)
    if day.day >= last_sunday.day: return 0
    days_remaining = last_sunday.day - day.day - 1
    weeks_remaining = days_remaining // DAYS_IN_WEEK
    return weeks_remaining + 1 # 1 for current week


def get_last_sunday_in_month(day, localtz):
    """Returns the last Sunday in the current month."""
    end_of_month = get_next_month(day, localtz)
    days_from_sunday = end_of_month.weekday() + 1
    return end_of_month - timedelta(days=days_from_sunday)


def get_days_in_month(year, month):
    """Returns number of days in the month provided."""
    return monthrange(year, month)[1]


def increment_time(day, timeunit, duration):
    """Increments day by duration of unit timeunit."""
    if timeunit == HOURS: return day + timedelta(hours=duration)
    elif timeunit == MINUTES: return day + timedelta(minutes=duration)


def decrement_time(day, timeunit, duration):
    """Decrements day by duration of unit timeunit."""
    if timeunit == HOURS: return day - timedelta(hours=duration)
    elif timeunit == MINUTES: return day - timedelta(minutes=duration)
