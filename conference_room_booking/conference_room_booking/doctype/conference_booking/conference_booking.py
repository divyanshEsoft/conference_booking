# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, get_time


class ConferenceBooking(Document):

    def validate(self):

        self.set_defaults()
        self.validate_management_reserved_room()
        self.validate_booking_time()
        self.validate_overlapping_booking()


# ----------------------------------------------------
# DEFAULT VALUES (Future-proofing)
# ----------------------------------------------------

    def set_defaults(self):
        # Auto set booked by
        if not self.booked_by:
            self.booked_by = frappe.session.user


# ----------------------------------------------------
# Reserved Room Permission Check
# ----------------------------------------------------

    def validate_management_reserved_room(self):

        if not self.conference_room:
            return

        room = frappe.get_doc("Conference Room", self.conference_room)

        if room.is_active:
            frappe.throw("This conference room is inactive and cannot be booked.")

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

        # Full day booking support
        if self.full_day:
            self.start_time = "00:00:00"
            self.end_time = "23:59:59"
            return
        
        # Start & End Time mandatory
        if not self.start_time or not self.end_time:
            frappe.throw("Start Time and End Time are required.")

        start_time = get_time(self.start_time)
        end_time = get_time(self.end_time)

        #  End time must be after start time
        if end_time <= start_time:
            frappe.throw("End Time must be after Start Time.")

        # #  Optional: Office hours restriction (future ready)
        # office_start = get_time("09:00:00")
        # office_end = get_time("19:00:00")

        # if start_time < office_start or end_time > office_end:
        #     frappe.throw("Bookings are allowed only between 9 AM and 7 PM.")


# ----------------------------------------------------
# Overlapping Booking Validation
# ----------------------------------------------------

    def validate_overlapping_booking(self):

        # If required fields missing → skip
        if not self.conference_room or not self.booking_date:
            return

        # Skip validation for cancelled bookings
        if self.status == "Cancelled":
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








