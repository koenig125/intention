"""Model to provide basic functions for scheduling same days/times."""

import numpy as np
from datetime import timedelta
from dateutil.parser import parse
from intention_app.scheduling.utils.datetime_utils import DAY, WEEK, MONTH, parse_datetime
from intention_app.scheduling.utils.scheduling_utils import get_number_periods
from intention_app.scheduling.utils.googleapi_utils import create_event

MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7


def consolidate_busy_times(period, period_start_time, period_end_time, localtz, busy_times):
    minutes_in_period = get_minutes_in_period(period)
    minute_map = make_minute_map(period, minutes_in_period)
    if period != "MONTH": minute_map_filled = consolidate(busy_times, localtz, period_start_time, minute_map, minutes_in_period)
    else: minute_map_filled = month_consolidate(busy_times, localtz, period_start_time, minute_map)
    return convert_map_to_times(period_start_time, period_end_time, minute_map_filled, localtz)


def month_consolidate(busy_times, localtz, period_start_time, minute_map):
    first_seven_days_week_nums = get_first_seven_days_week_nums(period_start_time)
    for i in range(len(busy_times)):
        busy_start = parse_datetime(busy_times[i]['start']).astimezone(localtz)
        busy_end = parse_datetime(busy_times[i]['end']).astimezone(localtz)

        day_index = get_day_index(busy_start)
        busy_week_num = get_week_number_for_day(busy_start)
        if busy_start.day > 28 or busy_week_num < first_seven_days_week_nums[day_index]: continue
        divisor = get_month_divisor(busy_start, period_start_time, busy_week_num, first_seven_days_week_nums)
        if not divisor: continue

        start_minute = int(minutes_between(period_start_time, busy_start, localtz) % divisor)
        end_minute = int(minutes_between(period_start_time, busy_end, localtz) % divisor)
        minute_map[int(start_minute):int(end_minute)] = False
    return minute_map


def get_first_seven_days_week_nums(period_start_time):
    first_seven_days_week_nums = [0] * DAYS_IN_WEEK
    for i in range(DAYS_IN_WEEK):
        day = period_start_time + timedelta(days=i)
        first_seven_days_week_nums[get_day_index(day)] = get_week_number_for_day(day)
    return first_seven_days_week_nums


def get_week_number_for_day(day):
    return (day.day - 1) // DAYS_IN_WEEK


def get_day_index(day):
    return (day.weekday() + 1) % DAYS_IN_WEEK


def get_month_divisor(busy_start, period_start_time, busy_week_num, first_seven_days_week_nums):
    if busy_start.month == period_start_time.month: return float('inf')
    minutes_to_original_day = get_minutes_back_to_original_day(busy_start, period_start_time)
    minutes_to_subtract = get_week_number_difference_minutes(busy_week_num, first_seven_days_week_nums, busy_start)
    total_minutes = minutes_to_original_day - minutes_to_subtract
    if (busy_start - timedelta(minutes=total_minutes)) < period_start_time: return None
    return total_minutes


def get_minutes_back_to_original_day(busy_start, period_start_time):
    index_diff = busy_start.weekday() - period_start_time.weekday()
    days_to_original = index_diff if index_diff >= 0 else DAYS_IN_WEEK + index_diff
    original_day = period_start_time + timedelta(days=days_to_original)
    day_difference = (busy_start.date() - original_day.date()).days
    minutes = day_difference * HOURS_IN_DAY * MINUTES_IN_HOUR
    return minutes


def get_week_number_difference_minutes(busy_week_num, first_seven_days_week_nums, busy_start):
    day_index = get_day_index(busy_start)
    first_seven_day_week_num = first_seven_days_week_nums[day_index]
    week_number_diff = busy_week_num - first_seven_day_week_num
    return week_number_diff * DAYS_IN_WEEK * HOURS_IN_DAY * MINUTES_IN_HOUR


def get_minutes_in_period(period):
    if period == DAY: return MINUTES_IN_HOUR * HOURS_IN_DAY
    elif period == WEEK: return MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_WEEK
    elif period == MONTH: return MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_WEEK * 4


def make_minute_map(period, minutes_in_period):
    if period == DAY: return np.ones(minutes_in_period, dtype=bool)
    elif period == WEEK: return np.ones(minutes_in_period, dtype=bool)
    elif period == MONTH: return np.ones(minutes_in_period, dtype=bool)


def consolidate(busy_times, localtz, period_start_time, minute_map, minutes_in_period):
    for i in range(len(busy_times)):
        busy_start = parse_datetime(busy_times[i]['start']).astimezone(localtz)
        busy_end = parse_datetime(busy_times[i]['end']).astimezone(localtz)
        start_minute = minutes_between(period_start_time, busy_start, localtz) % minutes_in_period
        end_minute = minutes_between(period_start_time, busy_end, localtz) % minutes_in_period
        if end_minute < start_minute:
            minute_map[start_minute:] = False
            minute_map[:end_minute] = False
        else:
            minute_map[start_minute:end_minute] = False
    return minute_map


def convert_map_to_times(period_start_time, period_end_time, minute_map_filled, localtz):
    busy_minutes = np.where(minute_map_filled == False)[0]
    busy_start = busy_minutes[0]
    busy_end = busy_minutes[0]
    busy_times = []
    for i in range(1, len(busy_minutes)):
        if busy_minutes[i] - busy_minutes[i-1] != 1:
            busy_end = busy_minutes[i-1] + 1
            busy_times.append(create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time, localtz))
            busy_start = busy_minutes[i]
    if busy_end != busy_minutes[-1] + 1:
        busy_end = busy_minutes[-1] + 1
        busy_times.append(create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time, localtz))
    return busy_times


def minutes_between(start_time, end_time, localtz):
    minutes = int((end_time - start_time).total_seconds()) // 60
    if not isdst(start_time, localtz) and isdst(end_time, localtz): return minutes + 60
    elif isdst(start_time, localtz) and not isdst(end_time, localtz): return minutes - 60
    else: return minutes


def isdst(dt, localtz):
    dt_loc = localtz.localize(dt.replace(tzinfo=None))
    return bool(dt_loc.dst())


def create_busy_chunk(busy_start, busy_end, period_start_time, period_end_time, localtz):
    start_time = period_start_time + timedelta(minutes=int(busy_start))
    end_time = period_start_time + timedelta(minutes=int(busy_end))
    if not isdst(period_start_time, localtz) and isdst(start_time, localtz):
        start_time -= timedelta(hours=1)
        end_time -= timedelta(hours=1)
    if isdst(period_start_time, localtz) and not isdst(start_time, localtz):
        start_time += timedelta(hours=1)
        end_time += timedelta(hours=1)
    if start_time < period_start_time and end_time > period_end_time:
        start_time -= timedelta(days=1)
        end_time -= timedelta(days=1)
    return {
        'start': start_time.isoformat(),
        'end': end_time.isoformat()
    }


def copy_events_for_each_period(events, period, period_start_time, name, localtz):
    num_periods = get_number_periods(period_start_time, period, localtz)
    all_events = events.copy()
    for event in events:
        busy_start = parse(event['start']['dateTime'])
        busy_end = parse(event['end']['dateTime'])
        for i in range(1, num_periods):
            delta = get_period_timedelta(period, i)
            new_start = busy_start + delta
            new_end = busy_end + delta
            if isdst(new_start, localtz):
                new_start -= timedelta(hours=1)
                new_end -= timedelta(hours=1)
            all_events.append(create_event(name, new_start, new_end))
    return all_events


def get_period_timedelta(period, num_periods):
    if period == "DAY": return timedelta(days=num_periods)
    if period == "WEEK": return timedelta(weeks=num_periods)
    if period == "MONTH": return None  # TODO: Decide on strategy for month.