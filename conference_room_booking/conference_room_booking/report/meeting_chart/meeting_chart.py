import frappe
from frappe.utils import formatdate, format_time, getdate, get_time, time_diff_in_seconds

def execute(filters=None):
	if not filters or not filters.get("booking_date"):
		return [], []

	booking_date = filters.get("booking_date")
	
	bookings = frappe.get_all("Conference Booking", 
		filters={"booking_date": booking_date, "status": ("not in", ["Cancelled", "Draft"]), "docstatus": ("!=", 2)},
		fields=["name", "conference_room", "meeting_title", "group_name", "client_name", "meeting_type", 
				"full_day", "start_time", "end_time", "status"],
		order_by="start_time asc"
	)

	rooms = frappe.get_all("Conference Room", 
		fields=["name", "booking_start_time", "booking_end_time"], 
		order_by="name asc"
	)
	
	# group by room
	room_bookings_raw = {}
	for r in rooms:
		room_bookings_raw[r.name] = []
	for b in bookings:
		if b.conference_room in room_bookings_raw:
			room_bookings_raw[b.conference_room].append(b)

	room_bookings = {}
	for r in rooms:
		actual_bookings = room_bookings_raw.get(r.name, [])
		
		if not r.booking_start_time or not r.booking_end_time:
			room_bookings[r.name] = actual_bookings
			continue
			
		# Availability logic
		processed = []
		current_cursor = r.booking_start_time
		
		for b in actual_bookings:
			# Check gap before this booking
			if b.start_time and b.start_time > current_cursor:
				# inject free slot
				processed.append(frappe._dict({
					"group_name": "Free",
					"client_name": "",
					"meeting_title": "Free",
					"meeting_type": "",
					"start_time": current_cursor,
					"end_time": b.start_time,
					"status": "Available",
					"is_free": True
				}))
			
			processed.append(b)
			if b.end_time:
				current_cursor = max(current_cursor, b.end_time)
				
		# Check gap after last booking
		if r.booking_end_time > current_cursor:
			processed.append(frappe._dict({
				"group_name": "Free",
				"client_name": "",
				"meeting_title": "Free",
				"meeting_type": "",
				"start_time": current_cursor,
				"end_time": r.booking_end_time,
				"status": "Available",
				"is_free": True
			}))
			
		if not processed and r.booking_start_time < r.booking_end_time:
			# Case for entirely free day
			processed.append(frappe._dict({
				"group_name": "Free",
				"client_name": "",
				"meeting_title": "Free",
				"meeting_type": "",
				"start_time": r.booking_start_time,
				"end_time": r.booking_end_time,
				"status": "Available",
				"is_free": True
			}))
			
		room_bookings[r.name] = processed

	# find max meetings
	max_meetings = 3
	for r_name, b_list in room_bookings.items():
		if len(b_list) > max_meetings:
			max_meetings = len(b_list)

	html = f'''
	<style>
		.meeting-chart-table {{
			width: 100%;
			border-collapse: collapse;
			margin-top: 15px;
			font-family: inherit;
			font-size: 13px;
		}}
		.meeting-chart-table th, .meeting-chart-table td {{
			border: 1px solid #d1d8dd;
			padding: 8px;
			text-align: center;
			vertical-align: middle;
			height: 35px;
		}}
		.meeting-chart-table th {{
			background-color: #fcfcfc;
			font-weight: 600;
			color: #555;
			border-bottom: 2px solid #eaeeef;
		}}
		/* Premium Subtle Colors */
		.td-green {{ background-color: #f0fff4 !important; color: #2f855a !important; font-weight: 500; border-left: 3px solid #68d391 !important; }}
		.td-orange {{ background-color: #fffaf0 !important; color: #9c4221 !important; font-weight: 500; border-left: 3px solid #f6ad55 !important; }}
		.td-blue {{ background-color: #ebf8ff !important; color: #2b6cb0 !important; font-weight: 500; border-left: 3px solid #63b3ed !important; }}
		
		/* Status Colors */
		.status-reserved {{ color: #d69e2e; font-weight: 600; }}
		.status-confirmed {{ color: #3182ce; font-weight: 600; }}
		.status-completed {{ color: #718096; font-weight: 600; }}
		.status-available {{ color: #38a169; font-weight: 600; font-style: italic; }}
		
		.room-header {{ background-color: #fff; font-weight: bold; text-align: left; color: #1a202c; }}
		.time-header {{ background-color: #fff; font-weight: bold; text-align: left; color: #718096; font-size: 11px; }}
	</style>

	<div class="table-responsive">
	<table class="meeting-chart-table">
		<thead>
			<tr>
				<th rowspan="2" style="width: 200px; text-align: left;">Dt {formatdate(booking_date, "dd/mm/yyyy")}</th>
	'''
	def get_ordinal(n):
		if 11 <= (n % 100) <= 13: return 'th'
		return ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
		
	for i in range(max_meetings):
		html += f'<th colspan="3" style="border-bottom: 1px solid #eee;">{i+1}{get_ordinal(i+1)} Meeting</th>'
	
	html += '</tr><tr>'
	for i in range(max_meetings):
		html += '<th style="font-size: 11px; color: #999;">Group Name</th><th style="font-size: 11px; color: #999;">Client Name</th><th style="font-size: 11px; color: #999;">Status</th>'
	html += '</tr></thead><tbody>'

	for room in rooms:
		r_name = room.name
		b_list = room_bookings.get(r_name, [])
		
		row1 = f'<tr><td class="room-header" style="padding-left: 15px;">{r_name}</td>'
		row2 = f'<tr><td class="time-header" style="padding-left: 15px;">Time / Type</td>'
		
		cells_added = 0
		col_idx = 0
		while col_idx < len(b_list):
			b = b_list[col_idx]
			
			g_name = b.group_name or ""
			c_name = b.client_name or ""
			m_title = b.meeting_title or ""
			
			full_text = f"{g_name} {c_name} {m_title}".lower()
			
			def fmt_time(t):
				if not t: return ""
				if hasattr(t, 'total_seconds'):
					tot_sec = int(t.total_seconds())
				else:
					tot_sec = t.hour * 3600 + t.minute * 60 + t.second if hasattr(t, 'hour') else 0
					
				h = tot_sec // 3600
				m = (tot_sec % 3600) // 60
				p = "am" if h < 12 else "pm"
				h12 = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
				return f"{h12}.{m:02d} {p}"

			if b.full_day:
				time_str = "Full Day"
			else:
				st = fmt_time(b.start_time)
				et = fmt_time(b.end_time)
				time_str = f"{st} - {et}" if st else ""
				if st and not et:
					time_str = f"{st} Onward"
			
			m_type = b.meeting_type or ""
			b_status = b.status or ""
			status_class = f"status-{b_status.lower()}"

			if b.get("is_free"):
				# Dynamic Free Label
				if col_idx == 0 and len(b_list) > 1:
					label = f"Free until {et}"
				elif col_idx == len(b_list) - 1 and len(b_list) > 1:
					label = f"Free from {st}"
				elif len(b_list) == 1:
					label = "Free for the Day"
				else:
					label = f"Free ({st} - {et})"
				
				row1 += f'<td colspan="3" rowspan="2" class="td-green" style="font-size: 14px;">{label}</td>'
				cells_added += 1
				col_idx += 1
			elif "boss" in full_text:
				remaining_meetings = max_meetings - cells_added
				colspan = remaining_meetings * 3
				display_text = m_title if m_title else (g_name if g_name else c_name)
				row1 += f'<td colspan="{colspan}" rowspan="2" class="td-orange" style="font-size: 14px;">{display_text}</td>'
				cells_added += remaining_meetings
				col_idx = len(b_list)
				break
			elif "empty" in full_text:
				display_text = g_name if g_name else (m_title if m_title else c_name)
				row1 += f'<td colspan="3" rowspan="2" class="td-green" style="font-size: 14px;">{display_text}</td>'
				cells_added += 1
				col_idx += 1
			else:
				row1 += f'<td>{g_name}</td><td>{c_name}</td><td><span class="{status_class}">{b_status}</span></td>'
				row2 += f'<td>{time_str}</td><td>{m_type}</td><td></td>'
				cells_added += 1
				col_idx += 1

		while cells_added < max_meetings:
			row1 += f'<td></td><td></td><td></td>'
			row2 += f'<td></td><td></td><td></td>'
			cells_added += 1
		
		row1 += '</tr>'
		row2 += '</tr>'
		html += row1 + row2

	html += '</tbody></table></div>'

	return [], [], html
