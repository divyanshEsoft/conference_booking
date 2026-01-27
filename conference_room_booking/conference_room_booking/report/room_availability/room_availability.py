# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


# Copyright (c) 2026, e.Soft Technologies
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate

# =====================================================
# REPORT EXECUTE
# =====================================================
def execute(filters=None):

    filters = filters or {}

    from_date = filters.get("from_date") or nowdate()
    to_date = filters.get("to_date") or from_date

    columns = [
        {
            "label": "Conference Room",
            "fieldname": "conference_room",
            "fieldtype": "Link",
            "options": "Conference Room",
            "width": 200,
        },
        {
            "label": "Capacity",
            "fieldname": "capacity",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": "Has Projector",
            "fieldname": "has_projector",
            "fieldtype": "Check",
            "width": 110,
        },
        {
            "label": "Buffer Time (Minutes)",
            "fieldname": "buffer_minutes",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "Availability",
            "fieldname": "availability",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Is Active",
            "fieldname": "is_active",
            "fieldtype": "Check",
            "width": 100,
        },
    ]

    data = []

    rooms = frappe.get_all(
        "Conference Room",
        fields=[
            "name",
            "capacity",
            "is_active",
            "has_projector",
            "buffer_minutes",
        ]
    )

    for room in rooms:

        # 🔶 MULTI-DAY + NULL-SAFE BOOKING CHECK
        bookings = frappe.db.sql(
            """
            SELECT full_day
            FROM `tabConference Booking`
            WHERE
                conference_room = %(room)s
                AND status IN ('Confirmed', 'Reserved')
                AND booking_date <= %(to_date)s
                AND COALESCE(booking_end_date, booking_date) >= %(from_date)s
            """,
            {
                "room": room.name,
                "from_date": from_date,
                "to_date": to_date,
            },
            as_dict=True,
        )

        # -------------------------------------------------
        # AVAILABILITY LOGIC (UNCHANGED & CORRECT)
        # -------------------------------------------------
        if not room.is_active:
            availability = "Inactive"
        elif not bookings:
            availability = "Available"
        elif any(b.full_day for b in bookings):
            availability = "Fully Booked"
        else:
            availability = "Reserved"

        data.append({
            "conference_room": room.name,
            "capacity": room.capacity,
            "has_projector": room.has_projector,
            "buffer_minutes": room.buffer_minutes,
            "availability": availability,
            "is_active": room.is_active,
        })

    return columns, data



# import frappe
# from frappe.utils import nowdate


# def execute(filters=None):
#     columns = [
#         {
#             "label": "Conference Room",
#             "fieldname": "conference_room",
#             "fieldtype": "Link",
#             "options": "Conference Room",
#             "width": 200,
#         },
#         {
#             "label": "Availability",
#             "fieldname": "availability",
#             "fieldtype": "Data",
#             "width": 150,
#         },
#         {
#             # 🔢 REQUIRED FOR DASHBOARD CHART
#             "label": "Count",
#             "fieldname": "count",
#             "fieldtype": "Int",
#             "width": 80,
#         },
#     ]

#     data = []
#     today = nowdate()

#     # Fetch all conference rooms
#     rooms = frappe.get_all(
#         "Conference Room",
#         fields=["name"]
#     )

#     for room in rooms:
#         # Fetch today's active bookings
#         bookings = frappe.get_all(
#             "Conference Booking",
#             filters={
#                 "conference_room": room.name,
#                 "booking_date": today,
#                 "status": ["in", ["Confirmed", "Reserved"]],
#             },
#             fields=["full_day"]
#         )

#         # Availability logic
#         if not bookings:
#             availability = "Available"
#         elif any(b.full_day for b in bookings):
#             availability = "Fully Booked"
#         else:
#             availability = "Reserved"

#         # ✅ NORMALIZE VALUE (VERY IMPORTANT)
#         availability = availability.strip().title()

#         data.append({
#             "conference_room": room.name,
#             "availability": availability,
#             "count": 1,  # one row per room
#         })

#     return columns, data
