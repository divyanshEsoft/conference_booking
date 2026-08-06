# Copyright (c) 2026, e.Soft Techonoligies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days
from conference_room_booking.conference_room_booking.doctype.conference_booking.conference_booking import get_available_rooms


class TestConferenceBooking(FrappeTestCase):

	def setUp(self):
		frappe.db.delete("Conference Booking", {"conference_room": ["like", "Test Room%"]})
		frappe.db.delete("Conference Room", {"name": ["like", "Test Room%"]})

		self.room = frappe.get_doc({
			"doctype": "Conference Room",
			"room_name": "Test Room A",
			"capacity": 10,
			"is_active": 1,
			"buffer_minutes": 15,
			"booking_start_time": "08:00:00",
			"booking_end_time": "20:00:00"
		}).insert(ignore_permissions=True)

	def test_buffer_minutes_in_get_available_rooms(self):
		test_date = add_days(today(), 1)
		
		# Create booking from 10:00:00 to 11:00:00
		booking = frappe.get_doc({
			"doctype": "Conference Booking",
			"conference_room": self.room.name,
			"booking_date": test_date,
			"start_time": "10:00:00",
			"end_time": "11:00:00",
			"status": "Reserved",
			"custom_no_of_attendees": 5,
			"client_name": "Test Client"
		}).insert(ignore_permissions=True)

		# Check room availability at 11:00:00 to 12:00:00 (within 15-min buffer)
		available_rooms = get_available_rooms(
			"Conference Room", "", "", 0, 20,
			{
				"booking_date": test_date,
				"start_time": "11:00:00",
				"end_time": "12:00:00",
				"full_day": 0
			}
		)
		available_room_names = [r[0] for r in available_rooms]
		self.assertNotIn(self.room.name, available_room_names)

		# Check room availability at 11:15:00 to 12:15:00 (after 15-min buffer)
		available_rooms_after = get_available_rooms(
			"Conference Room", "", "", 0, 20,
			{
				"booking_date": test_date,
				"start_time": "11:15:00",
				"end_time": "12:15:00",
				"full_day": 0
			}
		)
		available_room_names_after = [r[0] for r in available_rooms_after]
		self.assertIn(self.room.name, available_room_names_after)

		doc = frappe.new_doc("Conference Booking")
		roles = doc.get_allowed_roles()
		self.assertTrue(len(roles) > 0)

	def test_draft_booking_overlap_validation(self):
		test_date = add_days(today(), 2)

		# Create initial booking
		b1 = frappe.get_doc({
			"doctype": "Conference Booking",
			"conference_room": self.room.name,
			"booking_date": test_date,
			"start_time": "14:00:00",
			"end_time": "15:00:00",
			"status": "Reserved",
			"custom_no_of_attendees": 5,
			"client_name": "Test Client"
		}).insert(ignore_permissions=True)

		# Attempt overlapping booking in draft
		b2 = frappe.get_doc({
			"doctype": "Conference Booking",
			"conference_room": self.room.name,
			"booking_date": test_date,
			"start_time": "14:30:00",
			"end_time": "15:30:00",
			"status": "Draft",
			"custom_no_of_attendees": 5,
			"client_name": "Test Client 2"
		})

		self.assertRaises(frappe.ValidationError, b2.insert, ignore_permissions=True)
