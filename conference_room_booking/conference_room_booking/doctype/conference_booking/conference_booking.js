// Copyright (c) 2026, e.Soft Techonoligies and contributors
// For license information, please see license.txt

if (!frappe.conference_rooms_cache) {
	frappe.conference_rooms_cache = {};
}

// Intercept get_link_title to format Conference Room links in edit mode/autocomplete inputs
if (!frappe.utils._original_get_link_title) {
	frappe.utils._original_get_link_title = frappe.utils.get_link_title;
	frappe.utils.get_link_title = function (doctype, name) {
		if (doctype === "Conference Room" && name) {
			if (frappe.conference_rooms_cache[name]) {
				return frappe.conference_rooms_cache[name];
			}
		}
		return frappe.utils._original_get_link_title(doctype, name);
	};
}

frappe.form.link_formatters["Conference Room"] = function (value, doc, docfield) {
	if (!value) return value;
	if (frappe.conference_rooms_cache[value]) {
		return frappe.conference_rooms_cache[value];
	}

	// Fetch asynchronously and refresh the field
	frappe.db.get_value("Conference Room", value, ["room_name", "capacity"])
		.then(r => {
			if (r && r.message) {
				let name = r.message.room_name || value;
				let cap = r.message.capacity;
				let display = cap ? `${name} - Capacity: ${cap}` : name;
				frappe.conference_rooms_cache[value] = display;
				frappe.utils.add_link_title("Conference Room", value, display);
				if (cur_frm && cur_frm.doc && cur_frm.refresh_field) {
					cur_frm.refresh_field(docfield.fieldname);
				}
			}
		});

	return value;
};

frappe.ui.form.on("Conference Booking", {
	setup(frm) {
		// Filter rooms based on selected date and time
		frm.set_query("conference_room", function () {
			return {
				query: "conference_room_booking.conference_room_booking.doctype.conference_booking.conference_booking.get_available_rooms",
				filters: {
					booking_date: frm.doc.booking_date,
					start_time: frm.doc.start_time,
					end_time: frm.doc.end_time,
					full_day: frm.doc.full_day || 0,
					current_booking: frm.doc.name
				}
			};
		});
	},

	onload(frm) {
		// Store original time values when form loads
		frm._original_start_time = frm.doc.start_time;
		frm._original_end_time = frm.doc.end_time;
		frm.__confirmed_change = false;

		// Pre-populate link formatter cache for the selected room
		if (frm.doc.conference_room) {
			frappe.db.get_value("Conference Room", frm.doc.conference_room, ["room_name", "capacity"])
				.then(r => {
					if (r && r.message) {
						let name = r.message.room_name || frm.doc.conference_room;
						let cap = r.message.capacity;
						let display = cap ? `${name} - Capacity: ${cap}` : name;
						frappe.conference_rooms_cache[frm.doc.conference_room] = display;
						frappe.utils.add_link_title("Conference Room", frm.doc.conference_room, display);
						frm.refresh_field("conference_room");
					}
				});
		}

		if (frm.is_new() && (!frm.doc.booked_by || frm.doc.booked_by === '{user}')) {
			frm.set_value('booked_by', frappe.session.user);
		}

		if (frm.is_new() && !frm.doc.group_name) {
			frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["employee_name", "department"])
				.then(r => {
					if (r && r.message) {
						let name = r.message.employee_name;
						let dept = r.message.department;
						frm.set_value('group_name', dept ? `${name} - ${dept}` : name);
					} else {
						frappe.db.get_value("User", frappe.session.user, "full_name")
							.then(u => {
								let name = (u && u.message && u.message.full_name) || frappe.session.user;
								frm.set_value('group_name', name);
							});
					}
				});
		}

		frm.set_df_property('booked_by', 'read_only', 1);
		if (frm.fields_dict.booked_by && frm.fields_dict.booked_by.input) {
			$(frm.fields_dict.booked_by.input).prop('readonly', true);
		}

		frm.set_df_property('group_name', 'read_only', 1);
		if (frm.fields_dict.group_name && frm.fields_dict.group_name.input) {
			$(frm.fields_dict.group_name.input).prop('readonly', true);
		}
	},

	refresh(frm) {
		// Restrict date picker to today and future (disables clicking previous dates)
		frm.set_df_property('booking_date', 'datepicker_options', {
			minDate: new Date()
		});

		// Force booked_by to be read-only
		frm.set_df_property('booked_by', 'read_only', 1);
		if (frm.fields_dict.booked_by && frm.fields_dict.booked_by.input) {
			$(frm.fields_dict.booked_by.input).prop('readonly', true);
		}

		// Force group_name to be read-only
		frm.set_df_property('group_name', 'read_only', 1);
		if (frm.fields_dict.group_name && frm.fields_dict.group_name.input) {
			$(frm.fields_dict.group_name.input).prop('readonly', true);
		}
	},

	booking_date(frm) {
		validate_date(frm);
		refresh_room_selection(frm);
	},

	validate(frm) {
		if (frm.doc.name && frm.doc.name !== 'new' && !frm.__confirmed_change) {
			let changes = [];
			if (frm.doc.start_time !== frm._original_start_time) {
				const action = frm.doc.start_time > frm._original_start_time ? 'postpone' : 'prepone';
				changes.push(__('start time ({0})', [action]));
			}
			if (frm.doc.end_time !== frm._original_end_time) {
				const action = frm.doc.end_time > frm._original_end_time ? 'postpone' : 'prepone';
				changes.push(__('end time ({0})', [action]));
			}

			if (changes.length > 0) {
				frappe.validated = false;
				frappe.confirm(
					__('Are you sure you want to change the {0}? This will update the booking.', [changes.join(' ' + __('and') + ' ')]),
					() => {
						frm.__confirmed_change = true;
						frm.save();
					}
				);
			}
		}
	},

	start_time(frm) {
		refresh_room_selection(frm);
		validate_room_hours(frm);
	},

	end_time(frm) {
		refresh_room_selection(frm);
		validate_room_hours(frm);
	},

	full_day(frm) {
		refresh_room_selection(frm);
	},
	
	conference_room(frm) {
		validate_room_hours(frm);
		if (frm.doc.conference_room) {
			frappe.db.get_value("Conference Room", frm.doc.conference_room, ["room_name", "capacity"])
				.then(r => {
					if (r && r.message) {
						let name = r.message.room_name || frm.doc.conference_room;
						let cap = r.message.capacity;
						let display = cap ? `${name} - Capacity: ${cap}` : name;
						frappe.conference_rooms_cache[frm.doc.conference_room] = display;
						frappe.utils.add_link_title("Conference Room", frm.doc.conference_room, display);
						frm.refresh_field("conference_room");
					}
				});
		}
	}
});

function validate_date(frm) {
	if (frm.doc.booking_date && frappe.datetime.get_diff(frm.doc.booking_date, frappe.datetime.nowdate()) < 0) {
		frappe.msgprint(__('Booking Date cannot be in the past'));
		frm.set_value('booking_date', '');
	}
}

function refresh_room_selection(frm) {
	// If date and times are set, clear room if it's no longer available (optional UX)
	// But mainly we just want to ensure the list is fresh when they click it
	if (frm.doc.booking_date && (frm.doc.full_day || (frm.doc.start_time && frm.doc.end_time))) {
		// Room query will handle the filtering when the user clicks the field
	}
}

function validate_room_hours(frm) {
	if (!frm.doc.conference_room || frm.doc.full_day) return;
	if (!frm.doc.start_time && !frm.doc.end_time) return;

	// Helper: convert "HH:MM:SS" or "HH:MM:SS.ffffff" to total seconds
	function timeToSeconds(t) {
		if (!t) return null;
		const parts = String(t).split(':');
		const h = parseInt(parts[0]) || 0;
		const m = parseInt(parts[1]) || 0;
		const s = parseFloat(parts[2]) || 0;
		return h * 3600 + m * 60 + s;
	}

	frappe.db.get_value("Conference Room", frm.doc.conference_room, ["booking_start_time", "booking_end_time"])
		.then(r => {
			if (r && r.message) {
				let start_limit = r.message.booking_start_time;
				let end_limit = r.message.booking_end_time;

				if (start_limit && end_limit) {
					const roomOpen = timeToSeconds(start_limit);
					const roomClose = timeToSeconds(end_limit);

					if (frm.doc.start_time && timeToSeconds(frm.doc.start_time) < roomOpen) {
						// Format the limit nicely (strip microseconds)
						const limitDisplay = String(start_limit).split('.')[0];
						frappe.msgprint(__('Start time cannot be before room opening time ({0})', [limitDisplay]));
						frm.set_value('start_time', '');
					}
					if (frm.doc.end_time && timeToSeconds(frm.doc.end_time) > roomClose) {
						const limitDisplay = String(end_limit).split('.')[0];
						frappe.msgprint(__('End time cannot be after room closing time ({0})', [limitDisplay]));
						frm.set_value('end_time', '');
					}
				}
			}
		});
}
