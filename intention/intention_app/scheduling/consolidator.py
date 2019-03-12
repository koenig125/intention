"""Module to consolidate busy time ranges across multiple periods.

Handles logic needed to consolidate free busy information from
multiple periods of a user calendar into a single period range.

Exported Functions
------------------
consolidate_multiple_periods(busy_ranges, first_period_start, first_period_end, period, localtz)
"""

import numpy as np
from datetime import timedelta
from intention_app.scheduling.utils.datetime_utils import add_timedelta, get_weekday_index, get_week_number, \
    is_dst, DAY, WEEK, MONTH, SECONDS_IN_MINUTE, MINUTES_IN_HOUR, HOURS_IN_DAY, DAYS_IN_WEEK
from intention_app.scheduling.utils.scheduling_utils import get_range_freebusy

# Number days in month consolidation.
DAYS_IN_MONTH_ARRAY = 28

MINUTES_IN_DAY = HOURS_IN_DAY * MINUTES_IN_HOUR
MINUTES_IN_WEEK = MINUTES_IN_DAY * DAYS_IN_WEEK


def consolidate_multiple_periods(busy_ranges, first_period_start, first_period_end, period, localtz):
    """Returns list of busy time ranges consolidated across mutliple periods."""
    minutes_in_period = _get_minutes_in_period(period)
    minute_array = _make_minute_array(period, minutes_in_period)
    if period == MONTH: _consolidate_months(busy_ranges, first_period_start, minute_array, localtz)
    else: _consolidate_days_or_weeks(busy_ranges, first_period_start, minutes_in_period, minute_array, localtz)
    return _convert_array_to_timeranges(minute_array, first_period_start, first_period_end, localtz)


def _get_minutes_in_period(period):
    """Returns number of minutes in full period based on period provided."""
    if period == DAY: return MINUTES_IN_HOUR * HOURS_IN_DAY
    elif period == WEEK: return MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_WEEK
    elif period == MONTH: return MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_MONTH_ARRAY


def _make_minute_array(period, minutes_in_period):
    """Returns array of True values of size minutes_in_period."""
    if period == DAY: return np.ones(minutes_in_period, dtype=bool)
    elif period == WEEK: return np.ones(minutes_in_period, dtype=bool)
    elif period == MONTH: return np.ones(minutes_in_period, dtype=bool)


def _consolidate_days_or_weeks(busy_ranges, first_period_start, minutes_in_period, minute_array, localtz):
    """Populates minute array for days or weeks with values set to False for busy ranges."""
    for i in range(len(busy_ranges)):
        busy_start, busy_end = get_range_freebusy(i, busy_ranges, localtz)
        start_minute = int(_get_minutes_between(first_period_start, busy_start, localtz) % minutes_in_period)
        end_minute = int(_get_minutes_between(first_period_start, busy_end, localtz) % minutes_in_period)
        minute_array[start_minute:end_minute] = False
        if end_minute < start_minute:
            minute_array[start_minute:] = False
            minute_array[:end_minute] = False


def _consolidate_months(busy_ranges, first_period_start, minute_array, localtz):
    """Populates minute array for months with values set to False for busy ranges."""
    first_seven_days_week_nums = _get_first_seven_days_week_nums(first_period_start)
    for i in range(len(busy_ranges)):
        busy_start, busy_end = get_range_freebusy(i, busy_ranges, localtz)
        busy_day_week_num = get_week_number(busy_start)
        orig_day = first_seven_days_week_nums[get_weekday_index(busy_start)][0]
        orig_day_week_num = first_seven_days_week_nums[get_weekday_index(busy_start)][1]
        if busy_day_week_num < orig_day_week_num or busy_start.day > DAYS_IN_MONTH_ARRAY: continue
        modulo = _get_month_modulo(first_period_start, busy_start, orig_day, busy_day_week_num, orig_day_week_num)
        if (busy_start - timedelta(minutes=modulo)) < first_period_start: continue
        start_minute = int(_get_minutes_between(first_period_start, busy_start, localtz) % modulo)
        end_minute = int(_get_minutes_between(first_period_start, busy_end, localtz) % modulo)
        minute_array[start_minute:end_minute] = False


def _convert_array_to_timeranges(minute_array_filled, first_period_start, first_period_end, localtz):
    """Returns list of busy time ranges corresponding to minute indices with values set to False."""
    busy_ranges = []
    busy_minutes = [int(x) for x in np.where(minute_array_filled == False)[0]]
    start_minute, end_minute = busy_minutes[0], busy_minutes[0]
    for i in range(1, len(busy_minutes)):
        if busy_minutes[i] - busy_minutes[i-1] != 1:
            end_minute = busy_minutes[i-1] + 1
            busy_ranges.append(_create_range(start_minute, end_minute, first_period_start, first_period_end, localtz))
            start_minute = busy_minutes[i]
    if end_minute != busy_minutes[-1] + 1:
        end_minute = busy_minutes[-1] + 1
        busy_ranges.append(_create_range(start_minute, end_minute, first_period_start, first_period_end, localtz))
    return busy_ranges


def _create_range(start_minute, end_minute, first_period_start, first_period_end, localtz):
    """Returns busy time ranges incremented from the provided period start time."""
    busy_start = add_timedelta(timedelta(minutes=start_minute), first_period_start, localtz)
    busy_end = add_timedelta(timedelta(minutes=end_minute), first_period_start, localtz)
    if busy_start < first_period_start and busy_end > first_period_end:
        busy_start -= timedelta(days=1)
        busy_end -= timedelta(days=1)
    return {
        'start': busy_start.isoformat(),
        'end': busy_end.isoformat()
    }


def _get_minutes_between(start_time, end_time, localtz):
    """Returns number of minutes between the provided start and end times."""
    minutes = (end_time - start_time).total_seconds() // SECONDS_IN_MINUTE
    if not is_dst(start_time, localtz) and is_dst(end_time, localtz): return minutes + MINUTES_IN_HOUR
    elif is_dst(start_time, localtz) and not is_dst(end_time, localtz): return minutes - MINUTES_IN_HOUR
    else: return minutes


def _get_first_seven_days_week_nums(start_day):
    """Returns list containing the day provided and 6 proceeding days with their week numbers."""
    week_nums = [(None, None)] * DAYS_IN_WEEK
    for i in range(DAYS_IN_WEEK):
        day = start_day + timedelta(days=i)
        weekday_index = get_weekday_index(day)
        week_nums[weekday_index] = (day, get_week_number(day))
    return week_nums


def _get_month_modulo(period_start_time, future_day, orig_day, future_day_week_num, orig_day_week_num):
    """Returns the modulo needed to convert day in future month to corresponding day in current month.

    For example, if future day is 3rd Monday of March and current month is January, will find minutes
    needed to convert 3rd Monday of March to the 3rd Monday of January when used as modulus operator.
    """
    if future_day.month == period_start_time.month: return float('inf')
    minutes_between_days = (future_day.date() - orig_day.date()).days * MINUTES_IN_DAY
    minutes_between_week_nums = (future_day_week_num - orig_day_week_num) * MINUTES_IN_WEEK
    return minutes_between_days - minutes_between_week_nums
