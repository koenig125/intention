"""Module to manipulate datetime objects.

Manipulates datetime objects over days, weeks, and months.

Exported Functions
------------------
make_day_start(day)
make_day_end(day)
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
get_day_start_end_times(day, timerange)
increment_time(day, timeunit, duration)
decrement_time(day, timeunit, duration)
add_timedelta(td, dt, localtz)
parse_datetime(dt_str)
is_dst(dt, localtz)
get_week_number(day)
get_weekday_index(day)
get_month_timedelta(day, num_periods, localtz)
"""

from datetime import timedelta
from pytz import timezone
from calendar import monthrange
from dateutil.parser import parse

# Basic time rates
SECONDS_IN_MINUTE, MINUTES_IN_HOUR, HOURS_IN_DAY, DAYS_IN_WEEK = 60, 60, 24, 7

# Day bounding hours
DAY_START_HOUR, DAY_END_HOUR = 8, 1

# Time zones
utc = timezone('UTC')

# Time units
HOURS, MINUTES = "HOURS", "MINUTES"

# Time periods
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"

# Time ranges
MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"

# Timerange hours
AFTERNOON_START, EVENING_START = 12, 18 # Military time.
MORNING_HOURS = {'start': DAY_START_HOUR, 'end': AFTERNOON_START}
AFTERNOON_HOURS = {'start': AFTERNOON_START, 'end': EVENING_START}
EVENING_HOURS = {'start': EVENING_START, 'end': DAY_END_HOUR}


def make_day_start(day):
    """Returns day set to start hour based on DAY_START_TIME, regardless of timerange.."""
    if day.hour < DAY_START_HOUR: # Time is past midnight. Likely want to reschedule previous day.
        day -= timedelta(days=1)
    return day.replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)


def make_day_end(day):
    """Returns day set to start hour based on DAY_END_TIME, regardless of timerange.."""
    if DAY_END_HOUR < DAY_START_HOUR and not day.hour < DAY_START_HOUR:
        day += timedelta(days=1) # DAY_END_HOUR is past midnight
    return day.replace(hour=DAY_END_HOUR, minute=0, second=0, microsecond=0)


def make_start_hour(day, timerange):
    """Returns day set to start hour based on timerange."""
    start_hour = DAY_START_HOUR
    if timerange == MORNING: start_hour = MORNING_HOURS['start']
    elif timerange == AFTERNOON: start_hour = AFTERNOON_HOURS['start']
    elif timerange == EVENING: start_hour = EVENING_HOURS['start']
    return day.replace(hour=start_hour, minute=0, second=0, microsecond=0)


def make_end_hour(day, timerange):
    """Returns day set to end hour based on timerange."""
    end_hour = DAY_END_HOUR
    if timerange == MORNING: end_hour = MORNING_HOURS['end']
    elif timerange == AFTERNOON: end_hour = AFTERNOON_HOURS['end']
    elif timerange == EVENING: end_hour = EVENING_HOURS['end']
    if end_hour == DAY_END_HOUR and DAY_END_HOUR < DAY_START_HOUR:
        day += timedelta(days=1) # Day end time is past midnight.
    return day.replace(hour=end_hour, minute=0, second=0, microsecond=0)


def make_next_hour(day):
    """Returns day set to hour proceeding the current hour."""
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
    """Returns day incremented by 24 hours. Converts to utc to account for daylight savings."""
    return (day.astimezone(utc) + timedelta(days=1)).astimezone(localtz)


def get_next_week(day, localtz):
    """Returns the Sunday of the next week. Converts to utc to account for daylight savings."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_week(day))).astimezone(localtz)


def get_next_month(day, localtz):
    """Returns the first day of the next month. Converts to utc to account for daylight savings."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_month(day))).astimezone(localtz)


def get_next_quarter(day, localtz):
    """Returns the first day of the next quarter. Converts to utc to account for daylight savings."""
    return (day.astimezone(utc) + timedelta(days=get_days_left_in_quarter(day))).astimezone(localtz)


def get_days_left_in_week(day):
    """Returns number of days left in the current week. Includes inputted day in count."""
    return DAYS_IN_WEEK - get_weekday_index(day)


def get_days_left_in_month(day):
    """Returns number of days left in the current month. Includes inputted day in count."""
    days_in_month = _get_days_in_month(day.year, day.month)
    return days_in_month - day.day + 1 # 1 for current day


def get_days_left_in_quarter(day):
    """Returns number of days left in the current quarter. Includes inputted day in count."""
    days_left = get_days_left_in_month(day)
    days_left += _get_days_in_month(day.year, day.month + 1)
    days_left += _get_days_in_month(day.year, day.month + 2)
    return days_left


def get_weeks_left_in_month(day, localtz):
    """Returns number of weeks left in the current month."""
    last_sunday = _get_last_sunday_in_month(day, localtz)
    if day.day >= last_sunday.day: return 0
    days_remaining = last_sunday.day - day.day - 1
    weeks_remaining = days_remaining // DAYS_IN_WEEK
    return weeks_remaining + 1 # 1 for current week


def get_day_start_end_times(day, timerange):
    """Returns start and end times of day provided based on timerange."""
    return get_start_of_day(day, timerange), get_end_of_day(day, timerange)


def increment_time(day, timeunit, duration):
    """Returns day incremented by duration of unit timeunit."""
    if timeunit == HOURS: return day + timedelta(hours=duration)
    elif timeunit == MINUTES: return day + timedelta(minutes=duration)


def decrement_time(day, timeunit, duration):
    """Returns day decremented by duration of unit timeunit."""
    if timeunit == HOURS: return day - timedelta(hours=duration)
    elif timeunit == MINUTES: return day - timedelta(minutes=duration)


def add_timedelta(td, dt, localtz):
    """Returns datetime incremented by timedelta, accounting for daylight savings."""
    return dt + td + _get_dst_correction(dt, dt + td, localtz)


def parse_datetime(dt_str):
    """Returns provided datetime string parsed into datetime object."""
    return parse(dt_str)


def is_dst(dt, localtz):
    """Returns whether or not datetime provided is in daylight savings time."""
    dt_loc = localtz.localize(dt.replace(tzinfo=None))
    return bool(dt_loc.dst())


def get_week_number(day):
    """Returns number of weeks preceding the day provided in the current month."""
    return (day.day - 1) // DAYS_IN_WEEK


def get_weekday_index(day):
    """Returns the weekday index of the day provided, zero-indexed from Sunday."""
    return (day.weekday() + 1) % DAYS_IN_WEEK


def get_month_timedelta(day, num_periods, localtz):
    """Returns the day num_periods months in the future that corresponds to the provided day.

    For example, if day is the 3rd Monday of January, get_month_timedelta(day, 2, localtz)
    will return the 3rd Monday of March. Raises an error if provided a day that is the 5th
    of its instance in the current month, ie the 5th Wednesday of January.
    """
    month_first_day = get_next_month(day, localtz)
    for i in range(num_periods - 1):
        month_first_day = get_next_month(day, localtz)
    day_weekday_idx = get_weekday_index(day)
    mth_weekday_idx = get_weekday_index(month_first_day)
    day_difference = day_weekday_idx - mth_weekday_idx
    days_to_target = (day_difference if day_difference >= 0
                      else DAYS_IN_WEEK + day_difference)
    return month_first_day + get_week_number(day) * DAYS_IN_WEEK + days_to_target


def _get_last_sunday_in_month(day, localtz):
    """Returns the last Sunday in the current month."""
    end_of_month = get_next_month(day, localtz)
    days_from_sunday = end_of_month.weekday() + 1
    return end_of_month - timedelta(days=days_from_sunday)


def _get_days_in_month(year, month):
    """Returns number of days in the month provided."""
    return monthrange(year, month)[1]


def _get_dst_correction(base_dt, new_dt, localtz):
    """Returns time correction if one datetime is in daylight savings and the other is not."""
    if not is_dst(base_dt, localtz) and is_dst(new_dt, localtz):
        return timedelta(hours=-1)
    elif is_dst(base_dt, localtz) and not is_dst(new_dt, localtz):
        return timedelta(hours=1)
    else:
        return timedelta(hours=0)
