"""Module to manipulate datetime objects.

Manipulates datetime objects over days, weeks, and months.

Exported Functions
------------------
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
make_start_hour(day, timerange)
make_end_hour(day, timerange)
make_day_start(day)
make_day_end(day)
make_next_hour(day)
get_timerange_start_end_time(day, timerange)
get_day_start_end_time(day)
add_timedelta(td, dt, localtz)
parse_datetime(dt_str)
is_dst(dt, localtz)
is_whole_hour(dt)
get_week_number(day)
get_weekday_index(day)
get_month_timedelta(day, num_periods, localtz)
get_get_28th_of_month(day, timerange, day_start_time, day_end_time)
convert_to_military(h, m, ap)
"""

from datetime import timedelta, time
from pytz import timezone
from calendar import monthrange
from dateutil.parser import parse

# Basic time rates
SECONDS_IN_MINUTE, MINUTES_IN_HOUR, HOURS_IN_DAY, DAYS_IN_WEEK = 60, 60, 24, 7

# Time zones
utc = timezone('UTC')

# Time units
HOURS, MINUTES = "HOURS", "MINUTES"

# Time periods
DAY, WEEK, MONTH = "DAY", "WEEK", "MONTH"

# Time ranges
MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"

# Timerange hours
AFTERNOON_START, EVENING_START = time(12), time(18) # Military time.


def get_start_of_day(day, timerange, day_start_time):
    """Returns day provided set to start hour."""
    return make_start_hour(day, timerange, day_start_time)


def get_start_of_next_day(day, timerange, localtz, day_start_time):
    """Returns the day after that provided set to start hour."""
    if day.time() < day_start_time: # Day is past midnight.
        return make_start_hour(day, timerange, day_start_time)
    else:
        return make_start_hour(get_next_day(day, localtz), timerange, day_start_time)


def get_start_of_next_week(day, timerange, localtz, day_start_time):
    """Returns the Sunday of the next week set to start hour."""
    return make_start_hour(get_next_week(day, localtz), timerange, day_start_time)


def get_start_of_next_month(day, timerange, localtz, day_start_time):
    """Returns the first day of the next month set to start hour."""
    return make_start_hour(get_next_month(day, localtz), timerange, day_start_time)


def get_end_of_day(day, timerange, day_start_time, day_end_time):
    """Returns the day provided set to end hour."""
    return make_end_hour(day, timerange, day_start_time, day_end_time)


def get_end_of_week(day, timerange, localtz, day_start_time, day_end_time):
    """Returns the Saturday of current week set to end hour."""
    last_day_of_week = get_next_week(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_week, timerange, day_start_time, day_end_time)


def get_end_of_month(day, timerange, localtz, day_start_time, day_end_time):
    """Returns the last day of the current month set to end hour."""
    last_day_of_month = get_next_month(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_month, timerange, day_start_time, day_end_time)


def get_end_of_quarter(day, timerange, localtz, day_start_time, day_end_time):
    """Returns the last day of the last month in the current quarter set to end hour."""
    last_day_of_quarter = get_next_quarter(day, localtz) - timedelta(days=1)
    return make_end_hour(last_day_of_quarter, timerange, day_start_time, day_end_time)


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


def make_start_hour(day, timerange, day_start_time):
    """Returns day set to start hour based on timerange."""
    start_time = day_start_time
    if timerange == AFTERNOON: start_time = AFTERNOON_START
    elif timerange == EVENING: start_time = EVENING_START
    return day.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)


def make_end_hour(day, timerange, day_start_time, day_end_time):
    """Returns day set to end hour based on timerange."""
    end_time = day_end_time
    if timerange == MORNING: end_time = AFTERNOON_START
    elif timerange == AFTERNOON: end_time = EVENING_START
    if end_time < day_start_time:
        day += timedelta(days=1) # Day end time is past midnight.
    return day.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)


def make_day_start(day, day_start_time):
    """Returns day set to start hour based on day_start_time, regardless of timerange."""
    if day.time() < day_start_time: # Time is past midnight. Likely want to reschedule previous day.
        day -= timedelta(days=1)
    return day.replace(hour=day_start_time.hour, minute=day_start_time.minute, second=0, microsecond=0)


def make_day_end(day, day_start_time, day_end_time):
    """Returns day set to start hour based on day_end_time, regardless of timerange."""
    if day_end_time < day_start_time and not day.time() < day_start_time:
        day += timedelta(days=1) # day_end_time is past midnight
    if not day_end_time < day_start_time and day.time() < day_start_time:
        day -= timedelta(days=1) # day.time() is past midnight
    return day.replace(hour=day_end_time.hour, minute=day_end_time.minute, second=0, microsecond=0)


def make_next_hour(day):
    """Returns day set to hour proceeding the current hour."""
    return day.replace(hour=day.hour, minute=0, second=0, microsecond=0) + timedelta(hours=1)


def get_timerange_start_end_time(day, timerange, day_start_time, day_end_time):
    """Returns start and end times of day provided based on timerange."""
    return get_start_of_day(day, timerange, day_start_time), get_end_of_day(day, timerange, day_start_time,day_end_time)


def get_day_start_end_time(day, day_start_time, day_end_time):
    """Returns start and end times of day provided based on day_start_time and day_end_time."""
    return make_day_start(day, day_start_time), make_day_end(day, day_start_time, day_end_time)


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


def is_whole_hour(dt):
    """Returns whether or not datetime provided is whole hour, ie 1:00, 2:00, etc."""
    return dt.minute == 0 and dt.second == 0 and dt.microsecond == 0


def get_week_number(day):
    """Returns number of weeks preceding the day provided in the current month."""
    return (day.day - 1) // DAYS_IN_WEEK


def get_weekday_index(day):
    """Returns the weekday index of the day provided, zero-indexed from Sunday."""
    return (day.weekday() + 1) % DAYS_IN_WEEK


def get_month_timedelta(day, num_periods, localtz):
    """Returns the timedelta to the day num_periods months in the future corresponding to the provided day.

    For example, if day is the 3rd Monday of January, get_month_timedelta(day, 2, localtz)
    will return the 3rd Monday of March. Raises an error if provided a day that is the 5th
    of its instance in the current month, ie the 5th Wednesday of January.
    """
    month_first_day = get_next_month(day, localtz)
    for i in range(num_periods - 1):
        month_first_day = get_next_month(month_first_day, localtz)
    day_weekday_idx = get_weekday_index(day)
    mth_weekday_idx = get_weekday_index(month_first_day)
    day_difference = day_weekday_idx - mth_weekday_idx
    days_to_target = (day_difference if day_difference >= 0
                      else DAYS_IN_WEEK + day_difference)
    total_days = (month_first_day - day).days + get_week_number(day) * DAYS_IN_WEEK + days_to_target
    return timedelta(days=total_days)


def get_28th_of_month(day, timerange, day_start_time, day_end_time):
    """Returns end of the 28th day of the current month realtive to day provided."""
    day = day.replace(day=28)
    return get_end_of_day(day, timerange, day_start_time, day_end_time)


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


def convert_to_military(h, m, ap):
    """Returns string of given hour, minute, and am/pm indicator converted to military time."""
    if h == 12 and ap == 'am': h = 0
    if ap == 'pm': h += 12
    return '%s:%s' % (h, m)