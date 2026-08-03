# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, get_time, get_datetime, now_datetime, cint


class ConferenceBooking(Document):

    def validate(self):

        self.set_defaults()
        self.set_group_name()
        self.set_calendar_datetimes()
        self.validate_management_reserved_room()
        self.validate_booking_time()
        self.validate_advance_booking_limit()
        self.validate_overlapping_booking()
        self.validate_capacity()
        self.validate_ownership()



    def set_group_name(self):
        if not self.booked_by:
            return

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": self.booked_by},
            ["employee_name", "department"],
            as_dict=True
        )

        if employee:
            person_name = employee.employee_name
            team_name = employee.department
        else:
            person_name = frappe.db.get_value("User", self.booked_by, "full_name") or self.booked_by
            team_name = None

        if team_name:
            self.group_name = f"{person_name} - {team_name}"
        else:
            self.group_name = person_name


    def set_calendar_datetimes(self):
        if self.booking_date and self.start_time:
            self.starts_on = get_datetime(f"{self.booking_date} {self.start_time}")

        if self.booking_date and self.end_time:
            self.ends_on = get_datetime(f"{self.booking_date} {self.end_time}")

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

        # Check against Room's allowed booking hours
        if self.conference_room:
            room = frappe.get_cached_doc("Conference Room", self.conference_room)
            if room.booking_start_time and room.booking_end_time:
                if start_time < get_time(room.booking_start_time):
                    frappe.throw(f"Start Time cannot be before Room's opening time ({room.booking_start_time})")
                
                if end_time > get_time(room.booking_end_time):
                    frappe.throw(f"End Time cannot be after Room's closing time ({room.booking_end_time})")

    def validate_advance_booking_limit(self):
        if not self.booking_date:
            return

        try:
            settings = frappe.get_single("Conference Booking Settings")
            enabled = settings.enable_advance_booking_restriction if settings.enable_advance_booking_restriction is not None else 1
            max_hours = cint(settings.max_advance_booking_hours) or 48
            configured_roles = [d.role for d in settings.allowed_roles if d.role] if settings.allowed_roles else []
        except Exception:
            enabled = 1
            max_hours = 48
            configured_roles = []

        if not enabled:
            return

        allowed_roles = configured_roles if configured_roles else ["Administrator", "System Manager" , "HR", "HR Manager"]
        user_roles = frappe.get_roles(frappe.session.user)

        # Authorized roles can bypass advance booking limit
        if any(role in user_roles for role in allowed_roles):
            return

        if self.start_time:
            booking_start_datetime = get_datetime(f"{self.booking_date} {self.start_time}")
        else:
            booking_start_datetime = get_datetime(f"{self.booking_date} 00:00:00")

        current_datetime = now_datetime()
        time_diff_hours = (booking_start_datetime - current_datetime).total_seconds() / 3600.0

        if time_diff_hours > max_hours:
            frappe.throw(
                f"You cannot book a conference room more than {max_hours} hours in advance. "
                "Only authorized roles can book beyond this limit."
            )



    def validate_capacity(self):
        if not self.conference_room or not self.custom_no_of_attendees:
            return

        room_capacity = frappe.db.get_value("Conference Room", self.conference_room, "capacity")
        if room_capacity and int(self.custom_no_of_attendees) > int(room_capacity):
            frappe.throw(
                f"Number of attendees ({self.custom_no_of_attendees}) cannot exceed "
                f"the selected conference room's capacity ({room_capacity})."
            )

    def validate_ownership(self):
        # Allow new documents to be created without this check
        if self.is_new():
            return
            
        if not getattr(self, "booked_by", None):
            return

        original_doc = self.get_doc_before_save()
        original_booker = original_doc.booked_by if original_doc else self.booked_by
        current_user = frappe.session.user
        
        # Administrator can override
        if current_user == "Administrator":
            return
            
        if original_booker != current_user:
            frappe.throw("You can only modify bookings that you have created.", frappe.PermissionError)


# ----------------------------------------------------
# Overlapping Booking Validation
# ----------------------------------------------------


    def validate_overlapping_booking(self):
        
        if not self.conference_room or not self.booking_date:
            return
        
        # Skip cancelled & draft bookings
        if self.status in ["Cancelled", "Draft"]:
            return
        

        # ------------------------------------------------
        # FULL DAY CONFLICT CHECK (NEW)
        # ------------------------------------------------
  
        # Case 1: Existing FULL DAY booking blocks everything

        full_day_conflict = frappe.db.exists(
            "Conference Booking",
            {
                "conference_room": self.conference_room,
                "booking_date": self.booking_date,
                "status": ["in", ["Confirmed", "Reserved"]],
                "name": ["!=", self.name],
                "full_day": 1,
            }
        )

        if full_day_conflict:
            frappe.throw("Room already booked for the selected date (Full Day Booking).")

        # Case 2: If CURRENT booking is full day → no other bookings allowed

        if self.full_day:
            any_booking_exists = frappe.db.exists(
                "Conference Booking",
                {
                    "conference_room": self.conference_room,
                    "booking_date": self.booking_date,
                    "status": ["in", ["Confirmed", "Reserved"]],
                    "name": ["!=", self.name],
                }
            )


            if any_booking_exists:
                frappe.throw(
                    "Cannot book full day because the room already has bookings."
                )

            # Full day validated → skip time overlap logic
            return
        

        # ------------------------------------------------
        # PARTIAL TIME OVERLAP CHECK (EXISTING + BUFFER)
        # ------------------------------------------------

        room = frappe.get_doc("Conference Room", self.conference_room)
        buffer_minutes = room.buffer_minutes or 0


        def time_to_minutes(t):
            t = get_time(t)
            return t.hour * 60 + t.minute
        
        start_minutes = time_to_minutes(self.start_time) - buffer_minutes
        end_minutes = time_to_minutes(self.end_time) + buffer_minutes




        overlapping_booking = frappe.db.sql(
            """
            SELECT name
            FROM `tabConference Booking`
            WHERE
                conference_room = %s
                AND booking_date = %s
                AND status IN ('Confirmed', 'Reserved')
                AND name != %s
                AND (
                    (TIME_TO_SEC(start_time) / 60) < %s
                    AND (TIME_TO_SEC(end_time) / 60) > %s
                )
            """,
            (
                self.conference_room,
                self.booking_date,
                self.name,
                end_minutes,
                start_minutes,
            ),
        )

        if overlapping_booking:
            frappe.throw(
                "Room already booked or buffer time conflict exists for the selected slot."
            )




    # def validate_overlapping_booking(self):

    #     if not self.conference_room or not self.booking_date:
    #         return

    #     # Skip cancelled & draft bookings
    #     if self.status in ["Cancelled", "Draft"]:
    #         return

    #     room = frappe.get_doc("Conference Room", self.conference_room)
    #     buffer_minutes = room.buffer_minutes or 0

    #     def time_to_minutes(t):
    #         t = get_time(t)
    #         return t.hour * 60 + t.minute

    #     start_minutes = time_to_minutes(self.start_time) - buffer_minutes
    #     end_minutes = time_to_minutes(self.end_time) + buffer_minutes

    #     overlapping_booking = frappe.db.sql(
    #         """
    #         SELECT name
    #         FROM `tabConference Booking`
    #         WHERE
    #             conference_room = %s
    #             AND booking_date = %s
    #             AND status IN ('Confirmed', 'Reserved')
    #             AND name != %s
    #             AND (
    #                 (TIME_TO_SEC(start_time) / 60) < %s
    #                 AND (TIME_TO_SEC(end_time) / 60) > %s
    #             )
    #         """,
    #         (
    #             self.conference_room,
    #             self.booking_date,
    #             self.name,
    #             end_minutes,
    #             start_minutes,
    #         ),
    #     )

    #     if overlapping_booking:
    #         frappe.throw(
    #             "Room already booked or buffer time conflict exists for the selected slot."
    #         )



    # def validate_overlapping_booking(self):

    #     # If required fields missing → skip
    #     if not self.conference_room or not self.booking_date:
    #         return

    #     # Skip cancelled & draft bookings
    #     if self.status in ["Cancelled", "Draft"]:
    #         return
        

    #     overlapping_booking = frappe.db.exists(
    #         "Conference Booking",
    #         {
    #             "conference_room": self.conference_room,
    #             "booking_date": self.booking_date,
    #             "status": ["in", ["Confirmed", "Reserved"]],
    #             "name": ["!=", self.name],
    #             "start_time": ["<", self.end_time],
    #             "end_time": [">", self.start_time],
    #         }
    #     )

    #     if overlapping_booking:
    #         frappe.throw("Room already booked for the selected time slot.")

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
    
    def after_insert(self):
        if not self.status or self.status == "Draft":
            self.status = "Reserved"
            self.db_set("status", "Reserved")

    # =========================================================
    # PROTECT COMPLETED BOOKINGS // Prevent editing completed bookings
    # =========================================================
    def before_update_after_submit(self):
        if self.status == "Completed":
            frappe.throw("Completed bookings cannot be modified.")

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_available_rooms(doctype, txt, searchfield, start, page_len, filters):
    booking_date = filters.get("booking_date")
    start_time = filters.get("start_time")
    end_time = filters.get("end_time")
    full_day = frappe.utils.cint(filters.get("full_day"))
    current_booking = filters.get("current_booking")

    if not booking_date:
        return []

    # 1. Identify occupied rooms for the given slot
    occupied_rooms_query = """
        SELECT DISTINCT conference_room
        FROM `tabConference Booking`
        WHERE
            booking_date = %s
            AND status IN ('Confirmed', 'Reserved','Completed')
            AND name != %s
            AND (
                full_day = 1
                OR %s = 1
                OR (
                    start_time < %s
                    AND end_time > %s
                )
            )
    """

    # If full_day is current selection, we check against ANY booking
    # Otherwise we check against full_day bookings OR overlapping time bookings
    check_start = end_time if not full_day else "23:59:59"
    check_end = start_time if not full_day else "00:00:00"

    occupied_rooms = frappe.db.sql(occupied_rooms_query, (
        booking_date,
        current_booking or "",
        full_day,
        check_start,
        check_end
    ), as_dict=True)

    occupied_room_names = [d.conference_room for d in occupied_rooms]

    # 2. Get all active rooms that are NOT in the occupied list
    rooms_filter = {"is_active": 1}

    if occupied_room_names:
        rooms_filter["name"] = ["not in", occupied_room_names]

    rooms = frappe.get_all(
        "Conference Room",
        filters=rooms_filter,
        fields=["name", "room_name", "capacity"],
    )

    # Filter by search text on room_name or name
    if txt:
        txt_lower = txt.lower()
        rooms = [r for r in rooms if txt_lower in (r.room_name or "").lower() or txt_lower in (r.name or "").lower()]

    # Return as list of [name, display_label] so Frappe shows Room Name - Capacity
    return [
        [r.name, f"{r.room_name} - Capacity: {r.capacity}" if r.capacity else r.room_name]
        for r in rooms
    ]


def update_reserved_to_completed():
    """
    Scheduled task (runs every 5 minutes)
    Updates booking status from 'Reserved' to 'Completed' when end time + buffer time has passed
    """
    from frappe.utils import now_datetime, get_datetime
    from datetime import timedelta

    current_datetime = now_datetime()

    # Find all Reserved bookings with required fields
    bookings_to_update = frappe.db.sql(
        """
        SELECT name, booking_date, end_time, conference_room
        FROM `tabConference Booking`
        WHERE
            status = 'Reserved'
            AND booking_date IS NOT NULL
            AND end_time IS NOT NULL
            AND conference_room IS NOT NULL
        """,
        as_dict=True
    )

    updated_count = 0

    for booking in bookings_to_update:
        # Get the room's buffer time
        room = frappe.get_cached_doc("Conference Room", booking.conference_room)
        buffer_minutes = room.buffer_minutes or 0

        # Calculate the end datetime for this booking
        booking_end_datetime = get_datetime(f"{booking.booking_date} {booking.end_time}")

        # Add buffer time to end datetime
        booking_end_with_buffer = booking_end_datetime + timedelta(minutes=buffer_minutes)

        # If end time + buffer has passed, update status to Completed
        if booking_end_with_buffer < current_datetime:
            frappe.db.set_value("Conference Booking", booking.name, "status", "Completed", update_modified=False)
            updated_count += 1

    if updated_count > 0:
        frappe.db.commit()
        frappe.logger().info(f"Updated {updated_count} bookings from Reserved to Completed (with buffer time)")
