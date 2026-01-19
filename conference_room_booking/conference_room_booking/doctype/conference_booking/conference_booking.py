# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ConferenceBooking(Document):

    def validate(self):
        self.validate_management_reserved_room()
        self.validate_booking_time()
        self.validate_overlapping_booking()

# ----------------------------------------------------
# Reserved Room Permission Check
# ----------------------------------------------------

    def validate_management_reserved_room(self):
        if not self.conference_room:
            return

        room = frappe.get_doc("Conference Room", self.conference_room)

        if not room.reserved_for_management:
            return

        allowed_roles = ["HR Manager", "Administrator", "System Manager"]
        user_roles = frappe.get_roles(frappe.session.user)

        if not any(role in user_roles for role in allowed_roles):
            frappe.throw(
                "This conference room is reserved for office/management use only. "
                "Only HR Manager, Administrator, or System Manager can book it."
            )

# ----------------------------------------------------
# Date & Time Validation
# ----------------------------------------------------

    def validate_booking_time(self):

        # Cannot book in the past
        if self.booking_date and getdate(self.booking_date) < getdate(nowdate()):
            frappe.throw("You cannot book a conference room in the past.")

        # Start & End Time mandatory
        if not self.start_time or not self.end_time:
            frappe.throw("Start Time and End Time are required.")

        # End time must be after start time
        if self.end_time <= self.start_time:
            frappe.throw("End Time must be after Start Time.")




# ----------------------------------------------------
# Overlapping Booking Validation
# ----------------------------------------------------

    def validate_overlapping_booking(self):

        # If required fields missing → skip
        if not self.conference_room or not self.booking_date:
            return

        overlapping_booking = frappe.db.exists(
            "Conference Booking",
            {
                "conference_room": self.conference_room,
                "booking_date": self.booking_date,
                "status": ["in", ["Confirmed", "Reserved"]],
                "name": ["!=", self.name],
                "start_time": ["<", self.end_time],
                "end_time": [">", self.start_time],
            }
        )

        if overlapping_booking:
            frappe.throw("Room already booked for the selected time slot.")








