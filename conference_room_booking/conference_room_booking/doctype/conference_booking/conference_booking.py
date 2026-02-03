# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (
    getdate,
    nowdate,
    get_time,
    get_datetime,
    now_datetime,
)
from datetime import timedelta


class ConferenceBooking(Document):

    # =========================================================
    # MAIN VALIDATE
    # =========================================================
    def validate(self):
        self.set_defaults()
        self.set_calendar_datetimes()
        self.validate_management_reserved_room()
        self.validate_projector_requirements()
        self.validate_booking_time()
        self.validate_overlapping_booking()

    # =========================================================
    # 🔶 NEW: MULTI-DAY DATE EXPANSION
    # =========================================================
    def get_booking_dates(self):
        """
        Returns list of dates between booking_date and booking_end_date (inclusive)
        """
        start = getdate(self.booking_date)
        end = getdate(self.booking_end_date or self.booking_date)

        dates = []
        while start <= end:
            dates.append(start)
            start += timedelta(days=1)

        return dates

    # =========================================================
    # CALENDAR DATETIME SUPPORT
    # =========================================================
    def set_calendar_datetimes(self):
        if self.booking_date and self.start_time:
            self.starts_on = get_datetime(f"{self.booking_date} {self.start_time}")

        if self.booking_end_date and self.end_time:
            self.ends_on = get_datetime(f"{self.booking_end_date} {self.end_time}")

    # =========================================================
    # DEFAULT VALUES
    # =========================================================
    def set_defaults(self):
        if not self.booked_by:
            self.booked_by = frappe.session.user

    # =========================================================
    # RESERVED ROOM PERMISSION
    # =========================================================
    def validate_management_reserved_room(self):
        if not self.conference_room:
            return

        room = frappe.get_doc("Conference Room", self.conference_room)

        if not room.is_active:
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

    # =========================================================
    # DATE & TIME VALIDATION
    # =========================================================
  
    # def validate_booking_time(self):

    #     """
    #     Validates booking date & time.
    #     - Prevents past bookings
    #     - Supports multi-day bookings
    #     - Handles full-day bookings cleanly
    #     - Safe for web + mobile APIs
    #     """

    #     if getdate(self.booking_date) < getdate(nowdate()):
    #         frappe.throw("You cannot book a conference room in the past.")

    #     if self.booking_end_date and getdate(self.booking_end_date) < getdate(self.booking_date):
    #         frappe.throw("Booking End Date cannot be before Start Date.")

    #     # Full day booking
    #     if self.full_day:
    #         self.start_time = "00:00:00"
    #         self.end_time = "23:59:59"
    #         return

    #     if not self.start_time or not self.end_time:
    #         frappe.throw("Start Time and End Time are required.")

    #     start_time = get_time(self.start_time)
    #     end_time = get_time(self.end_time)

    #     if end_time <= start_time:
    #         frappe.throw("End Time must be after Start Time.")

    #     if self.booking_date == nowdate():
    #         if get_time(self.start_time) <= get_time(now_datetime().time()):
    #             frappe.throw("Start Time must be in the future for today's bookings.")



    def validate_booking_time(self):
        """
        Validates booking date & time.
        - Prevents past bookings
        - Supports multi-day bookings
        - Handles full-day bookings cleanly
        - Safe for web + mobile APIs
        """

        # --------------------------------------------------
        # BASIC DATE VALIDATION
        # --------------------------------------------------
        if not self.booking_date:
            frappe.throw("Booking Start Date is required.")

        if getdate(self.booking_date) < getdate(nowdate()):
            frappe.throw("You cannot book a conference room in the past.")

        # --------------------------------------------------
        # BOOKING END DATE (MULTI-DAY SAFE)
        # --------------------------------------------------
        if not self.booking_end_date:
            # Auto-fix single day booking
            self.booking_end_date = self.booking_date

        if getdate(self.booking_end_date) < getdate(self.booking_date):
            frappe.throw("Booking End Date cannot be before Booking Start Date.")

        # --------------------------------------------------
        # FULL DAY BOOKING
        # --------------------------------------------------
        if self.full_day:
            self.start_time = "00:00:00"
            self.end_time = "23:59:59"
            return

        # --------------------------------------------------
        # TIME MANDATORY
        # --------------------------------------------------
        if not self.start_time or not self.end_time:
            frappe.throw("Start Time and End Time are required.")

        start_time = get_time(self.start_time)
        end_time = get_time(self.end_time)

        # --------------------------------------------------
        # TIME ORDER VALIDATION
        # --------------------------------------------------
        if end_time <= start_time:
            frappe.throw("End Time must be after Start Time.")

        # --------------------------------------------------
        # TODAY TIME VALIDATION (ONLY FOR SAME-DAY BOOKINGS)
        # --------------------------------------------------
        if (
            getdate(self.booking_date) == getdate(nowdate())
            and getdate(self.booking_end_date) == getdate(self.booking_date)
        ):
            current_time = get_time(now_datetime().time())

            if start_time <= current_time:
                frappe.throw("Start Time must be in the future for today's bookings.")


    # =========================================================
    # 🔶 UPDATED: MULTI-DAY OVERLAP VALIDATION
    # =========================================================
   
    # def validate_overlapping_booking(self):

    #     if not self.conference_room or not self.booking_date:
    #         return

    #     if self.status in ["Cancelled", "Draft"]:
    #         return

    #     room = frappe.get_doc("Conference Room", self.conference_room)
    #     buffer_minutes = room.buffer_minutes or 0

    #     def time_to_minutes(t):
    #         t = get_time(t)
    #         return t.hour * 60 + t.minute

    #     start_minutes = time_to_minutes(self.start_time) - buffer_minutes
    #     end_minutes = time_to_minutes(self.end_time) + buffer_minutes

    #     # 🔶 SAFETY CLAMP
    #     start_minutes = max(start_minutes, 0)
    #     end_minutes = min(end_minutes, 24 * 60)

    #     # 🔶 LOOP THROUGH EACH DAY
    #     for booking_day in self.get_booking_dates():

    #         # -------------------------------------------------
    #         # FULL DAY CONFLICT
    #         # -------------------------------------------------
    #         full_day_conflict = frappe.db.exists(
    #             "Conference Booking",
    #             {
    #                 "conference_room": self.conference_room,
    #                 "booking_date": booking_day,
    #                 "status": ["in", ["Confirmed", "Reserved"]],
    #                 "name": ["!=", self.name],
    #                 "full_day": 1,
    #             }
    #         )

    #         if full_day_conflict:
    #             frappe.throw(
    #                 f"Room already booked for full day on {booking_day}."
    #             )

    #         if self.full_day:
    #             any_booking = frappe.db.exists(
    #                 "Conference Booking",
    #                 {
    #                     "conference_room": self.conference_room,
    #                     "booking_date": booking_day,
    #                     "status": ["in", ["Confirmed", "Reserved"]],
    #                     "name": ["!=", self.name],
    #                 }
    #             )

    #             if any_booking:
    #                 frappe.throw(
    #                     f"Cannot book full day. Existing booking found on {booking_day}."
    #                 )

    #             continue  # Skip time overlap for full day

    #         # -------------------------------------------------
    #         # TIME OVERLAP CHECK
    #         # -------------------------------------------------
    #         overlapping_booking = frappe.db.sql(
    #             """
    #             SELECT name
    #             FROM `tabConference Booking`
    #             WHERE
    #                 conference_room = %s
    #                 AND booking_date = %s
    #                 AND status IN ('Confirmed', 'Reserved')
    #                 AND name != %s
    #                 AND (
    #                     (TIME_TO_SEC(start_time) / 60) < %s
    #                     AND (TIME_TO_SEC(end_time) / 60) > %s
    #                 )
    #             """,
    #             (
    #                 self.conference_room,
    #                 booking_day,
    #                 self.name,
    #                 end_minutes,
    #                 start_minutes,
    #             ),
    #         )

    #         if overlapping_booking:
    #             frappe.throw(
    #                 f"Room already booked or buffer conflict on {booking_day}."
    #             )


    def validate_overlapping_booking(self):
        """
        Validates overlapping bookings.
        - Status-aware (Draft → Reserved/Confirmed handled)
        - Multi-day safe
        - Full-day & partial-day rules enforced
        - Buffer time respected
        """

        if not self.conference_room or not self.booking_date:
            return

        # --------------------------------------------------
        # STATUS AWARE CHECK
        # --------------------------------------------------
        active_statuses = ["Reserved", "Confirmed"]

        # Detect status transition (Draft → Reserved/Confirmed)
        previous = self.get_doc_before_save()
        previous_status = previous.status if previous else None

        should_validate = (
            self.status in active_statuses or
            previous_status in active_statuses
        )

        if not should_validate:
            return

        # --------------------------------------------------
        # ROOM + BUFFER
        # --------------------------------------------------
        room = frappe.get_doc("Conference Room", self.conference_room)
        buffer_minutes = room.buffer_minutes or 0

        def time_to_minutes(t):
            t = get_time(t)
            return t.hour * 60 + t.minute

        # --------------------------------------------------
        # TIME WINDOW (BUFFER APPLIED)
        # --------------------------------------------------
        start_minutes = time_to_minutes(self.start_time) - buffer_minutes
        end_minutes = time_to_minutes(self.end_time) + buffer_minutes

        # Safety clamp
        start_minutes = max(start_minutes, 0)
        end_minutes = min(end_minutes, 24 * 60)

        # --------------------------------------------------
        # LOOP EACH BOOKING DAY (MULTI-DAY)
        # --------------------------------------------------
        for booking_day in self.get_booking_dates():

            # ----------------------------------------------
            # EXISTING FULL-DAY BLOCKS EVERYTHING
            # ----------------------------------------------
            full_day_exists = frappe.db.exists(
                "Conference Booking",
                {
                    "conference_room": self.conference_room,
                    "booking_date": booking_day,
                    "status": ["in", active_statuses],
                    "full_day": 1,
                    "name": ["!=", self.name],
                }
            )

            if full_day_exists:
                frappe.throw(
                    f"Conference room already booked for full day on {booking_day}."
                )

            # ----------------------------------------------
            # IF CURRENT IS FULL DAY → NO OTHER BOOKINGS
            # ----------------------------------------------
            if self.full_day:
                any_booking = frappe.db.exists(
                    "Conference Booking",
                    {
                        "conference_room": self.conference_room,
                        "booking_date": booking_day,
                        "status": ["in", active_statuses],
                        "name": ["!=", self.name],
                    }
                )

                if any_booking:
                    frappe.throw(
                        f"Cannot book full day. Existing booking found on {booking_day}."
                    )

                continue  # Skip time checks for full-day booking

            # ----------------------------------------------
            # PARTIAL TIME OVERLAP CHECK
            # ----------------------------------------------
            overlap = frappe.db.sql(
                """
                SELECT name
                FROM `tabConference Booking`
                WHERE
                    conference_room = %s
                    AND booking_date = %s
                    AND status IN ('Reserved', 'Confirmed')
                    AND name != %s
                    AND (
                        (TIME_TO_SEC(start_time) / 60) < %s
                        AND (TIME_TO_SEC(end_time) / 60) > %s
                    )
                """,
                (
                    self.conference_room,
                    booking_day,
                    self.name,
                    end_minutes,
                    start_minutes,
                ),
            )

            if overlap:
                frappe.throw(
                    f"Conference room already booked or buffer conflict on {booking_day}."
                )


    # =========================================================
    # PROJECTOR VALIDATION
    # =========================================================
    def validate_projector_requirements(self):
        if not self.conference_room or not self.projector_required:
            return

        room = frappe.get_doc("Conference Room", self.conference_room)

        if not room.has_projector:
            frappe.throw(
                "Projector is required for this meeting, "
                "but the selected conference room does not have one."
            )

    # =========================================================
    # PROTECT COMPLETED BOOKINGS // Prevent editing completed bookings
    # =========================================================
    def before_update_after_submit(self):
        if self.status == "Completed":
            frappe.throw("Completed bookings cannot be modified.")










