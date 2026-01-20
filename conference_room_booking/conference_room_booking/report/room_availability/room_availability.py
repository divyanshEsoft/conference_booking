# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data



import frappe
from frappe.utils import nowdate


def execute(filters=None):
    columns = [
        {
            "label": "Conference Room",
            "fieldname": "conference_room",
            "fieldtype": "Link",
            "options": "Conference Room",
            "width": 200,
        },
        {
            "label": "Availability",
            "fieldname": "availability",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            # 🔢 REQUIRED FOR DASHBOARD CHART
            "label": "Count",
            "fieldname": "count",
            "fieldtype": "Int",
            "width": 80,
        },
    ]

    data = []
    today = nowdate()

    # Fetch all conference rooms
    rooms = frappe.get_all(
        "Conference Room",
        fields=["name"]
    )

    for room in rooms:
        # Fetch today's active bookings
        bookings = frappe.get_all(
            "Conference Booking",
            filters={
                "conference_room": room.name,
                "booking_date": today,
                "status": ["in", ["Confirmed", "Reserved"]],
            },
            fields=["full_day"]
        )

        # Availability logic
        if not bookings:
            availability = "Available"
        elif any(b.full_day for b in bookings):
            availability = "Fully Booked"
        else:
            availability = "Reserved"

        # ✅ NORMALIZE VALUE (VERY IMPORTANT)
        availability = availability.strip().title()

        data.append({
            "conference_room": room.name,
            "availability": availability,
            "count": 1,  # one row per room
        })

    return columns, data
