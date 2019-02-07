# Given a list of events and a schedule, adds those events to the user's schedule.
#
# Params
# - event_list: a list of events currently on the user's calendar
# - form_data: a form containing the user's desired event
#
# Returns
# - new_event_list: an updated event_list with the added events
def schedule(event_list, form_data):
	# Currently only handle the "DAILY" case.
	if form_data['frequency'] != 'DAY':
		return event_list
	# Currently only adds events on the hour, and for one-hour increments.
	for i in range(0, 24):
		for event in event_list:
			if event.start == i:
				continue
			if event.end > i and event.end < i + 1:
				continue
		return event_list.append({'start' : i, 'end' : i+1})
	return event_list