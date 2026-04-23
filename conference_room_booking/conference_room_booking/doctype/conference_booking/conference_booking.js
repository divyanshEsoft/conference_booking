// Copyright (c) 2026, e.Soft Techonoligies and contributors
// For license information, please see license.txt

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

		if (frm.is_new() && (!frm.doc.booked_by || frm.doc.booked_by === '{user}')) {
			frm.set_value('booked_by', frappe.session.user);
		}

		frm.set_df_property('booked_by', 'read_only', 1);
		if (frm.fields_dict.booked_by && frm.fields_dict.booked_by.input) {
			$(frm.fields_dict.booked_by.input).prop('readonly', true);
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

	frappe.db.get_value("Conference Room", frm.doc.conference_room, ["booking_start_time", "booking_end_time"])
		.then(r => {
			if (r && r.message) {
				let start_limit = r.message.booking_start_time;
				let end_limit = r.message.booking_end_time;

				if (start_limit && end_limit) {
					if (frm.doc.start_time && frm.doc.start_time < start_limit) {
						frappe.msgprint(__('Start time cannot be before room opening time ({0})', [start_limit]));
						frm.set_value('start_time', '');
					}
					if (frm.doc.end_time && frm.doc.end_time > end_limit) {
						frappe.msgprint(__('End time cannot be after room closing time ({0})', [end_limit]));
						frm.set_value('end_time', '');
					}
				}
			}
		});
}
