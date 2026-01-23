# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


import frappe

def execute(filters=None):
    columns = [
        {
            "label": "Conference Room",
            "fieldname": "conference_room",
            "fieldtype": "Link",
            "options": "Conference Room",
            "width": 150,
            "grouped": 1,   # 👈 THIS LINE
        },
        {
            "label": "Meeting",
            "fieldname": "meeting",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Client",
            "fieldname": "client",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Start Time",
            "fieldname": "start_time",
            "fieldtype": "Time",
            "width": 90,
        },
        {
            "label": "End Time",
            "fieldname": "end_time",
            "fieldtype": "Time",
            "width": 90,
        },
        {
            "label": "Date",
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]

    data = frappe.db.sql("""
        SELECT
            conference_room AS conference_room,
            meeting_title AS meeting,
            client_name AS client,
            TIME_FORMAT(start_time, '%H:%i') AS start_time,
            TIME_FORMAT(end_time, '%H:%i') AS end_time,
            booking_date AS date,
            status AS status
        FROM `tabConference Booking`
        WHERE
            booking_date = CURDATE()
            AND status IN ('Confirmed', 'Reserved')
        ORDER BY
            conference_room,
            start_time
    """, as_dict=True)

    return columns, data
