# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


# import frappe

# def execute(filters=None):
#     columns = [
#         # {
#         #     label: "No",
#         #     fieldname: "idx",           
#         #     width: 40
#         # },
#         {
#             "label": "Conference Room",
#             "fieldname": "conference_room",
#             "fieldtype": "Link",
#             "options": "Conference Room",
#             # "width": 150,
#             "grouped": 1,   # for Room wise grouping
#         },
#         {
#             "label": "Meeting",
#             "fieldname": "meeting",
#             "fieldtype": "Data",
#             # "width": 150,
#         },
#         {
#             "label": "Client",
#             "fieldname": "client",
#             "fieldtype": "Data",
#             # "width": 150,
#         },
#         {
#             "label": "Booked By",            # 🔶 NEW COLUMN
#             "fieldname": "booked_by",
#             "fieldtype": "Data",
#             # "width": 140,
#         },
#         {
#             "label": "Start Time",
#             "fieldname": "start_time",
#             "fieldtype": "Time",
#             # "width": 90,
#         },
#         {
#             "label": "End Time",
#             "fieldname": "end_time",
#             "fieldtype": "Time",
#             # "width": 90,
#         },
#         {
#             "label": "Date",
#             "fieldname": "date",
#             "fieldtype": "Date",
#             # "width": 100,
#         },
#         {
#             "label": "Status",
#             "fieldname": "status",
#             "fieldtype": "Data",
#             # "width": 100,
#         },
#     ]

#     data = frappe.db.sql("""
#         SELECT
#             conference_room AS conference_room,
#             meeting_title AS meeting,
#             client_name AS client,
#             booked_by AS booked_by, 
#             TIME_FORMAT(start_time, '%H:%i') AS start_time,
#             TIME_FORMAT(end_time, '%H:%i') AS end_time,
#             booking_date AS date,
#             status AS status
#         FROM `tabConference Booking`
#         WHERE
#             booking_date = CURDATE()
#             AND status IN ('Confirmed', 'Reserved')
#         ORDER BY
#             conference_room,
#             start_time
#     """, as_dict=True)

#     return columns, data

# Copyright (c) 2026, e.Soft Technologies
# For license information, please see license.txt

# import frappe

# # =====================================================
# # REPORT EXECUTE
# # =====================================================
# def execute(filters=None):

#     filters = filters or {}

#     from_date = filters.get("from_date")
#     to_date = filters.get("to_date")

#     columns = [
#         {
#             "label": "Conference Room",
#             "fieldname": "conference_room",
#             "fieldtype": "Link",
#             "options": "Conference Room",
#             "grouped": 1,
#         },
#         {
#             "label": "Meeting",
#             "fieldname": "meeting",
#             "fieldtype": "Data",
#         },
#         {
#             "label": "Client",
#             "fieldname": "client",
#             "fieldtype": "Data",
#         },
#         {
#             "label": "Booked By",
#             "fieldname": "booked_by",
#             "fieldtype": "Data",
#         },
#         {
#             "label": "Start Time",
#             "fieldname": "start_time",
#             "fieldtype": "Time",
#         },
#         {
#             "label": "End Time",
#             "fieldname": "end_time",
#             "fieldtype": "Time",
#         },
#         {
#             "label": "Date",
#             "fieldname": "date",
#             "fieldtype": "Date",
#         },
#         {
#             "label": "Status",
#             "fieldname": "status",
#             "fieldtype": "Data",
#         },
#     ]

#     # 🔶 DEFAULT = TODAY
#     date_condition = "booking_date = CURDATE()"
#     values = {}

#     # 🔶 DATE RANGE SUPPORT
#     if from_date and to_date:
#         date_condition = "booking_date BETWEEN %(from_date)s AND %(to_date)s"
#         values = {
#             "from_date": from_date,
#             "to_date": to_date,
#         }

#     # 🔶 FIX: ESCAPE % IN TIME_FORMAT
#     data = frappe.db.sql(
#         f"""
#         SELECT
#             conference_room AS conference_room,
#             meeting_title AS meeting,
#             client_name AS client,
#             booked_by AS booked_by,
#             TIME_FORMAT(start_time, '%%H:%%i') AS start_time,
#             TIME_FORMAT(end_time, '%%H:%%i') AS end_time,
#             booking_date AS date,
#             status AS status
#         FROM `tabConference Booking`
#         WHERE
#             {date_condition}
#             AND status IN ('Confirmed', 'Reserved')
#         ORDER BY
#             conference_room,
#             booking_date,
#             start_time
#         """,
#         values,
#         as_dict=True,
#     )

#     return columns, data

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
            "grouped": 1,
        },
        {"label": "Meeting", "fieldname": "meeting", "fieldtype": "Data"},
        {"label": "Client", "fieldname": "client", "fieldtype": "Data"},
        {"label": "Booked By", "fieldname": "booked_by", "fieldtype": "Data"},
        {"label": "Start Time", "fieldname": "start_time", "fieldtype": "Time"},
        {"label": "End Time", "fieldname": "end_time", "fieldtype": "Time"},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date"},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data"},
    ]

    data = frappe.db.sql(
        """
        SELECT
            conference_room,
            meeting_title AS meeting,
            client_name AS client,
            booked_by,
            TIME_FORMAT(start_time, '%%H:%%i') AS start_time,
            TIME_FORMAT(end_time, '%%H:%%i') AS end_time,
            booking_date AS date,
            status
        FROM `tabConference Booking`
        WHERE
            booking_date <= %(to_date)s
            AND COALESCE(booking_end_date, booking_date) >= %(from_date)s
            AND status IN ('Confirmed', 'Reserved')
        ORDER BY
            conference_room,
            booking_date,
            start_time
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=True,
    )

    return columns, data
