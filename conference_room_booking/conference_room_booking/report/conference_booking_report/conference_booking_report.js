// Copyright (c) 2026, e.Soft Techonoligies and contributors
// For license information, please see license.txt

function cbr_can_book_past() {
	return frappe.user.has_role("System Manager") || 
	       frappe.user.has_role("HR Manager") || 
	       frappe.session.user === "Administrator";
}

frappe.query_reports["Conference Booking Report"] = {
	filters: [
		{
			fieldname: "booking_date",
			label: __("Booking Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			onchange: function () {
				let val = frappe.query_report.get_filter_value("booking_date");
				if (val && moment(val).isBefore(frappe.datetime.get_today(), 'day') && !cbr_can_book_past()) {
					frappe.msgprint(__("Only HR Managers and Administrators can select past booking dates. Setting date to today."));
					frappe.query_report.set_filter_value("booking_date", frappe.datetime.get_today());
				}
			}
		},
		{
			fieldname: "conference_room",
			label: __("Conference Room"),
			fieldtype: "Link",
			options: "Conference Room"
		},
		{
			fieldname: "has_projector",
			label: __("Has Projector"),
			fieldtype: "Check"
		}
	],

	before_refresh: function (report) {
		report.data = [];
		report.result = [];
		$(".report-wrapper .dt-wrapper, .report-wrapper .dt-container, .report-wrapper .frappe-datatable").hide();
		$("#cbr-container").remove();
	},

	onload: function (report) {
		report.report_settings.disable_cache = 1;

		if (!document.getElementById("cbr-styles")) {
			let style = document.createElement("style");
			style.id = "cbr-styles";
			style.textContent = cbr_get_styles();
			document.head.appendChild(style);
		}
	},

	after_datatable_render: function () {
		$(".report-wrapper .dt-wrapper, .report-wrapper .dt-container, .report-wrapper .frappe-datatable, .report-wrapper .datatable").hide();
		$("#cbr-container").remove();

		let raw = frappe.query_report.data;
		if (!raw) return;

		cbr_render_view(raw);
	}
};

/* ═══════════════════════════════════════════════════════════
   MAIN VIEW RENDERER
═══════════════════════════════════════════════════════════ */
function cbr_render_view(rooms) {
	let filter_vals = frappe.query_report.get_values() || {};
	let booking_date = filter_vals.booking_date || frappe.datetime.get_today();

	let html = `
	<div id="cbr-container" class="cbr-wrapper">

		<!-- Top Day Strip Selector -->
		<div class="cbr-day-strip-section">
			<div class="cbr-day-strip-title"><i class="fa fa-calendar-o"></i> SCHEDULE OVERVIEW</div>
			<div class="cbr-day-strip">
				${cbr_build_day_strip(booking_date)}
			</div>
		</div>

		<!-- Status Legend Bar -->
		<div class="cbr-legend-bar">
			<span class="cbr-legend-item"><span class="cbr-dot cbr-dot-available"></span> Available</span>
			<span class="cbr-legend-item"><span class="cbr-dot cbr-dot-booked"></span> Booked</span>
			<span class="cbr-legend-item"><span class="cbr-dot cbr-dot-past"></span> Past</span>
			<span class="cbr-legend-item"><span class="cbr-line-now"></span> Now</span>
		</div>

		<!-- Room Cards -->
		<div class="cbr-room-list">
			${rooms.map(room => cbr_build_room_card(room, booking_date)).join('')}
		</div>

		<!-- Bottom Action Bar -->
		<div class="cbr-bottom-bar">
			<div class="cbr-bottom-text">
				<strong>Need a meeting room?</strong><br>
				<span class="text-muted">Quickly book an available slot</span>
			</div>
			<button class="btn btn-primary cbr-btn-book" onclick="cbr_open_book_dialog()">
				<i class="fa fa-plus"></i> Book a Slot
			</button>
		</div>

	</div>`;

	$(".report-wrapper").append(html);
}

/* ═══════════════════════════════════════════════════════════
   DAY STRIP BUILDER (NO PAST DATES - 14 DAYS OVERVIEW)
═══════════════════════════════════════════════════════════ */
function cbr_build_day_strip(selected_date) {
	let today_str = frappe.datetime.get_today();
	let today = moment(today_str);
	let can_past = cbr_can_book_past();
	let days_html = "";

	// Start from selected_date if HR/Admin selected a past date, otherwise start from today
	let start_date = (can_past && moment(selected_date).isBefore(today, 'day')) ? moment(selected_date) : today;
	let end_date = moment(start_date).add(13, 'days');

	if (moment(selected_date).isAfter(end_date, 'day')) {
		end_date = moment(selected_date);
	}

	let curr = moment(start_date);
	while (curr.isSameOrBefore(end_date, 'day')) {
		let date_str = curr.format('YYYY-MM-DD');
		let day_name = curr.format('ddd').toUpperCase();
		let day_num = curr.format('DD');
		let is_active = (date_str === selected_date) ? "active" : "";

		days_html += `
		<div class="cbr-day-card ${is_active}" onclick="cbr_select_date('${date_str}')">
			<div class="cbr-day-name">${day_name}</div>
			<div class="cbr-day-num">${day_num}</div>
		</div>`;

		curr.add(1, 'days');
	}
	return days_html;
}

function cbr_select_date(date_str) {
	if (moment(date_str).isBefore(frappe.datetime.get_today(), 'day') && !cbr_can_book_past()) {
		frappe.show_alert({ message: __("Past dates cannot be selected."), indicator: "orange" });
		return;
	}
	frappe.query_report.set_filter_value('booking_date', date_str).then(() => {
		frappe.query_report.refresh();
	});
}

/* ═══════════════════════════════════════════════════════════
   ROOM CARD & TIMELINE TRACK BUILDER
═══════════════════════════════════════════════════════════ */
function cbr_build_room_card(room, selected_date) {
	let today_str = frappe.datetime.get_today();
	let is_today = (selected_date === today_str);
	let is_past_date = moment(selected_date).isBefore(today_str, 'day');
	let can_past = cbr_can_book_past();

	let now_time = moment();
	let current_minutes = now_time.hours() * 60 + now_time.minutes();

	let start_min = 10 * 60; // 10:00 AM
	let end_min = 22 * 60;   // 10:00 PM
	let total_mins = end_min - start_min;

	let now_pct = ((current_minutes - start_min) / total_mins) * 100;
	let show_now = is_today && (now_pct >= 0 && now_pct <= 100);
	let now_time_formatted = now_time.format('hh:mm A');

	let segments_html = "";
	let interval = 30;

	for (let m = start_min; m < end_min; m += interval) {
		let seg_start = m;
		let seg_end = m + interval;

		let is_past = is_past_date || (is_today && seg_end <= current_minutes);
		let bk_match = room.bookings.find(b => {
			let b_start = cbr_time_to_minutes(b.start_time_str);
			let b_end = cbr_time_to_minutes(b.end_time_str);
			return (seg_start < b_end && seg_end > b_start);
		});
		let is_booked = !!bk_match;

		let status_cls = is_booked ? "seg-booked" : (is_past ? "seg-past" : "seg-available");
		let slot_time_str = cbr_minutes_to_time(seg_start);
		let slot_12h = cbr_format_mins_to_12h(seg_start);

		let tooltip = slot_12h;
		if (is_booked && bk_match) {
			let bk_time = (bk_match.start_time_12h && bk_match.end_time_12h) 
				? `${bk_match.start_time_12h} – ${bk_match.end_time_12h}`
				: `${bk_match.start_time_str} – ${bk_match.end_time_str}`;
			tooltip = `Booked: ${bk_time} (${bk_match.client_name || bk_match.booked_by})`;
		} else if (is_past) {
			tooltip += can_past ? " (Past - HR/Admin Allowed)" : " (Past)";
		} else {
			tooltip += " (Available)";
		}

		let encoded_room = encodeURIComponent(room.room_id || '');
		let click_action = (is_past && !can_past)
			? "frappe.show_alert({message: __('Cannot book a room for a past date/time.'), indicator: 'orange'})"
			: (is_booked ? "" : `cbr_open_book_dialog(decodeURIComponent('${encoded_room}'), '${slot_time_str}')`);

		segments_html += `
		<div class="cbr-seg ${status_cls}" 
			 title="${tooltip}" 
			 onclick="${click_action}">
		</div>`;
	}

	let active_booking_html = "";
	if (room.bookings && room.bookings.length) {
		active_booking_html = room.bookings.map(bk => {
			let display_time = (bk.start_time_12h && bk.end_time_12h)
				? `${bk.start_time_12h} – ${bk.end_time_12h}`
				: `${bk.start_time_str} – ${bk.end_time_str}`;
			let group_text = bk.group_name ? ` &bull; ${bk.group_name}` : '';

			return `
			<div class="cbr-booking-info-strip" style="margin-top: 6px;">
				<div class="cbr-booking-info-text">
					<i class="fa fa-clock-o text-orange"></i> 
					<strong>Reserved: ${bk.client_name || bk.booked_by}</strong>${group_text}
					&bull; ${display_time} 
					<span class="badge badge-light" style="margin-left: 6px;">${bk.meeting_type || 'Internal'}</span>
				</div>
				<button class="btn btn-xs btn-default" onclick="frappe.set_route('Form', 'Conference Booking', '${bk.name}')">View Details</button>
			</div>`;
		}).join('');
	} else {
		active_booking_html = `
		<div class="cbr-booking-info-strip cbr-empty-hint">
			<span><i class="fa fa-info-circle ${is_past_date ? 'text-muted' : 'text-success'}"></i> ${is_past_date ? 'Past Date - Booking Closed' : 'Tap on any green slot to book'}</span>
		</div>`;
	}

	return `
	<div class="cbr-room-card">
		<div class="cbr-room-header">
			<div class="cbr-room-title">
				<h3>${room.room_name}</h3>
				<span class="cbr-capacity-badge"><i class="fa fa-users"></i> ${room.capacity}</span>
				${room.has_projector ? '<span class="cbr-badge-projector"><i class="fa fa-desktop"></i> Has Projector</span>' : ''}
			</div>
			<div class="cbr-status-pill">${is_past_date ? 'PAST DATE' : room.availability_status}</div>
		</div>

		<div class="cbr-timeline-scale">
			<span>10 AM</span><span>12 PM</span><span>2 PM</span><span>4 PM</span><span>6 PM</span><span>8 PM</span><span>10 PM</span>
		</div>

		<div class="cbr-timeline-track-wrap">
			<div class="cbr-timeline-track">
				${segments_html}
			</div>
			${show_now ? `
			<div class="cbr-now-line" style="left: ${now_pct}%;">
				<span class="cbr-now-pill">${now_time_formatted}</span>
			</div>` : ''}
		</div>

		${active_booking_html}
	</div>`;
}

function cbr_time_to_minutes(time_str) {
	if (!time_str) return 0;
	let parts = time_str.split(':');
	return parseInt(parts[0]) * 60 + parseInt(parts[1]);
}

function cbr_minutes_to_time(mins) {
	let h = Math.floor(mins / 60);
	let m = mins % 60;
	let h_str = h < 10 ? '0' + h : h;
	let m_str = m < 10 ? '0' + m : m;
	return `${h_str}:${m_str}:00`;
}

function cbr_format_mins_to_12h(mins) {
	let h = Math.floor(mins / 60);
	let m = mins % 60;
	let period = h < 12 ? 'AM' : 'PM';
	let h12 = h % 12;
	if (h12 === 0) h12 = 12;
	let m_str = m < 10 ? '0' + m : m;
	return `${h12}:${m_str} ${period}`;
}

/* ═══════════════════════════════════════════════════════════
   "BOOK A SLOT" DIALOG DRAWER
═══════════════════════════════════════════════════════════ */
function cbr_open_book_dialog(room_id, start_time) {
	let raw_data = frappe.query_report.data || [];
	if (!room_id && raw_data.length > 0) {
		room_id = raw_data[0].room_id || raw_data[0].name;
	}

	let filter_vals = frappe.query_report.get_values() || {};
	let today_str = frappe.datetime.get_today();
	let booking_date = filter_vals.booking_date || today_str;

	if (moment(booking_date).isBefore(today_str, 'day') && !cbr_can_book_past()) {
		booking_date = today_str;
	}

	start_time = start_time || "10:00:00";
	let start_mins = cbr_time_to_minutes(start_time);
	let default_end_time = cbr_minutes_to_time(start_mins + 60);

	let default_client = frappe.session.user_fullname || frappe.session.user || "";

	let d = new frappe.ui.Dialog({
		title: __('Book a Slot'),
		fields: [
			{
				fieldname: "conference_room",
				label: __("Conference Room"),
				fieldtype: "Link",
				options: "Conference Room",
				reqd: 1,
				onchange: function () {
					cbr_validate_capacity(d);
				}
			},
			{
				fieldname: "booking_date",
				label: __("Booking Date"),
				fieldtype: "Date",
				reqd: 1,
				onchange: function () {
					let val = d.get_value("booking_date");
					if (val && moment(val).isBefore(frappe.datetime.get_today(), 'day') && !cbr_can_book_past()) {
						frappe.msgprint(__("Only HR Managers and Administrators can select past booking dates."));
						d.set_value("booking_date", frappe.datetime.get_today());
					}
				}
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "start_time",
				label: __("Start Time"),
				fieldtype: "Time",
				reqd: 1,
				onchange: () => cbr_recalc_duration(d)
			},
			{
				fieldname: "end_time",
				label: __("End Time"),
				fieldtype: "Time",
				reqd: 1,
				onchange: () => cbr_recalc_duration(d)
			},
			{ fieldtype: "Section Break", label: __("Meeting Details") },
			{
				fieldname: "meeting_title",
				label: __("Meeting Title"),
				fieldtype: "Data"
			},
			{
				fieldname: "client_name",
				label: __("Client Name"),
				fieldtype: "Data",
				reqd: 1
			},
			{
				fieldname: "no_of_persons",
				label: __("Number of Persons / Attendees"),
				fieldtype: "Int",
				default: 1,
				reqd: 1,
				onchange: function () {
					cbr_validate_capacity(d);
				}
			},
			{
				fieldname: "group_name",
				label: __("Group / Team Name"),
				fieldtype: "Data",
				description: __("e.g. Sales Team")
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "meeting_type",
				label: __("Meeting Type"),
				fieldtype: "Select",
				options: ["Online", "Hybrid", "Internal", "Client Visit"],
				default: "Online",
				reqd: 1
			},
			{
				fieldname: "projector_required",
				label: __("Projector Required"),
				fieldtype: "Check"
			},
			{
				fieldname: "remarks",
				label: __("Remarks"),
				fieldtype: "Small Text"
			}
		],
		primary_action_label: __('Confirm Booking'),
		primary_action: function () {
			let data = d.get_values();
			if (!data) return;

			if (moment(data.booking_date).isBefore(frappe.datetime.get_today(), 'day') && !cbr_can_book_past()) {
				frappe.throw(__("Cannot book a conference room for a past date. Only HR Managers & Admins can book past slots."));
				return;
			}

			// Validate room capacity
			let room_obj = (frappe.query_report.data || []).find(r => r.room_id === data.conference_room || r.name === data.conference_room);
			if (room_obj && room_obj.capacity && data.no_of_persons > room_obj.capacity) {
				frappe.throw(__("Exceeds Capacity! <b>{0}</b> has a maximum capacity of <b>{1} persons</b>. You entered {2}.", [room_obj.room_name || data.conference_room, room_obj.capacity, data.no_of_persons]));
				return;
			}

			if (!data.group_name && data.no_of_persons) {
				data.group_name = `${data.no_of_persons} Attendees`;
			} else if (data.group_name && data.no_of_persons) {
				data.group_name = `${data.group_name} (${data.no_of_persons} Persons)`;
			}
			delete data.no_of_persons;

			data.doctype = "Conference Booking";
			data.status = "Reserved";
			data.booked_by = frappe.session.user_fullname || frappe.session.user;

			frappe.db.insert(data).then(doc => {
				frappe.show_alert({ message: __("Booking confirmed successfully!"), indicator: "green" });
				d.hide();
				frappe.query_report.refresh();
			});
		}
	});

	d.set_values({
		conference_room: room_id || "",
		booking_date: booking_date,
		start_time: start_time,
		end_time: default_end_time,
		client_name: default_client,
		no_of_persons: 1,
		meeting_type: "Online"
	});

	d.show();
	cbr_recalc_duration(d);
	cbr_validate_capacity(d);
}

function cbr_validate_capacity(dialog) {
	let room = dialog.get_value("conference_room");
	let persons = dialog.get_value("no_of_persons");
	if (room) {
		let room_obj = (frappe.query_report.data || []).find(r => r.room_id === room || r.name === room);
		if (room_obj && room_obj.capacity) {
			dialog.set_df_property("no_of_persons", "description", `Max capacity for ${room_obj.room_name || room}: <b>${room_obj.capacity} persons</b>`);
			if (persons && persons > room_obj.capacity) {
				frappe.msgprint({
					title: __("Exceeds Room Capacity"),
					message: __("<b>{0}</b> has a maximum capacity of <b>{1} persons</b>. You cannot book for {2} persons.", [room_obj.room_name || room, room_obj.capacity, persons]),
					indicator: "red"
				});
				dialog.set_value("no_of_persons", room_obj.capacity);
			}
		}
	}
}

function cbr_recalc_duration(dialog) {
	let start_time = dialog.get_value("start_time");
	let end_time = dialog.get_value("end_time");
	if (start_time && end_time) {
		let start_mins = cbr_time_to_minutes(start_time);
		let end_mins = cbr_time_to_minutes(end_time);
		let diff = end_mins - start_mins;
		if (diff > 0) {
			let hours = Math.floor(diff / 60);
			let mins = diff % 60;
			dialog.set_df_property('end_time', 'description', `Duration: ${hours}h ${mins}m`);
		} else {
			dialog.set_df_property('end_time', 'description', '');
		}
	}
}

/* ═══════════════════════════════════════════════════════════
   CSS STYLES
═══════════════════════════════════════════════════════════ */
function cbr_get_styles() {
	return `
	/* Hide standard datatable grid elements unconditionally for this report */
	.report-wrapper .dt-wrapper,
	.report-wrapper .dt-scroll-wrapper,
	.report-wrapper .dt-container,
	.report-wrapper .frappe-datatable,
	.report-wrapper .datatable { display:none !important; }

	.cbr-wrapper {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		padding: 16px 24px 80px;
		max-width: 1200px;
		margin: 0 auto;
	}

	.cbr-day-strip-section { margin-bottom: 20px; }
	.cbr-day-strip-title { font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; margin-bottom: 10px; }
	.cbr-day-strip { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px; }
	.cbr-day-card {
		background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
		padding: 10px 12px; min-width: 64px; flex: 1; text-align: center; cursor: pointer;
		transition: all 0.15s;
	}
	.cbr-day-card:hover { border-color: #2563eb; transform: translateY(-1px); }
	.cbr-day-card.active { background: #2563eb; color: #fff; border-color: #2563eb; box-shadow: 0 4px 12px rgba(37,99,235,0.25); }
	.cbr-day-name { font-size: 11px; font-weight: 700; text-transform: uppercase; }
	.cbr-day-num { font-size: 20px; font-weight: 800; line-height: 1.2; }

	.cbr-legend-bar { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; font-size: 12px; color: #475569; }
	.cbr-legend-item { display: flex; align-items: center; gap: 6px; font-weight: 500; }
	.cbr-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
	.cbr-dot-available { background: #22c55e; }
	.cbr-dot-booked { background: #f97316; }
	.cbr-dot-past { background: #cbd5e1; }
	.cbr-line-now { width: 3px; height: 14px; background: #2563eb; display: inline-block; border-radius: 2px; }

	.cbr-room-list { display: flex; flex-direction: column; gap: 16px; margin-bottom: 30px; }
	.cbr-room-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
	.cbr-room-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
	.cbr-room-title { display: flex; align-items: center; gap: 10px; }
	.cbr-room-title h3 { margin: 0; font-size: 17px; font-weight: 700; color: #0f172a; }
	.cbr-capacity-badge { font-size: 12px; color: #64748b; background: #f1f5f9; padding: 3px 8px; border-radius: 6px; }
	.cbr-badge-projector { font-size: 11px; color: #2563eb; background: #eff6ff; padding: 3px 8px; border-radius: 6px; }
	.cbr-status-pill { font-size: 11px; font-weight: 700; background: #dcfce7; color: #15803d; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; }

	.cbr-timeline-scale { display: flex; justify-content: space-between; font-size: 10px; font-weight: 600; color: #94a3b8; margin-bottom: 6px; padding: 0 4px; }
	.cbr-timeline-track-wrap { position: relative; margin-bottom: 14px; }
	.cbr-timeline-track { display: flex; height: 28px; border-radius: 8px; overflow: hidden; background: #f8fafc; border: 1px solid #e2e8f0; }
	.cbr-seg { flex: 1; border-right: 1px solid rgba(255,255,255,0.4); cursor: pointer; transition: opacity 0.15s; }
	.cbr-seg:hover { opacity: 0.8; }
	.seg-available { background: #86efac; }
	.seg-booked { background: #fb923c; }
	.seg-past { background: #e2e8f0; background-image: repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.05) 4px, rgba(0,0,0,0.05) 8px); }

	.cbr-now-line { position: absolute; top: -4px; bottom: -4px; width: 2px; background: #2563eb; z-index: 5; pointer-events: none; }
	.cbr-now-pill { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); background: #2563eb; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }

	.cbr-booking-info-strip { background: #f8fafc; border: 1px solid #f1f5f9; border-radius: 10px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; font-size: 12.5px; }
	.cbr-empty-hint { color: #64748b; font-size: 12px; }

	.cbr-bottom-bar {
		position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
		background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
		padding: 12px 24px; display: flex; align-items: center; gap: 30px;
		box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); z-index: 100; min-width: 480px; justify-content: space-between;
	}
	.cbr-bottom-text { font-size: 13px; line-height: 1.3; }
	.cbr-btn-book { padding: 8px 20px; font-weight: 600; border-radius: 10px; }
	`;
}
