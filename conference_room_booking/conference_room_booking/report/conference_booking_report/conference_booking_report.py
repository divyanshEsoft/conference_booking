# Copyright (c) 2026,
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate
from datetime import timedelta

def format_12h(time_val):
    if not time_val:
        return ""
    if isinstance(time_val, timedelta):
        total_seconds = int(time_val.total_seconds())
        h = (total_seconds // 3600) % 24
        m = (total_seconds % 3600) // 60
    elif isinstance(time_val, str):
        parts = time_val.split(':')
        h, m = int(parts[0]), int(parts[1])
    else:
        h, m = time_val.hour, time_val.minute

    period = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {period}"

def execute(filters=None):
    if not filters:
        filters = {}

    # Exact filter fieldnames: booking_date, conference_room, has_projector
    booking_date = filters.get("booking_date") or nowdate()
    conference_room = filters.get("conference_room")
    has_projector = filters.get("has_projector")

    # 1. Fetch Active Conference Rooms using exact fieldnames
    room_filters = {"is_active": 1}
    if conference_room:
        room_filters["name"] = conference_room
    if has_projector:
        room_filters["has_projector"] = 1

    rooms = frappe.get_all(
        "Conference Room",
        filters=room_filters,
        fields=[
            "name",
            "room_name",
            "floor_area",
            "capacity",
            "has_projector",
            "buffer_minutes",
            "booking_start_time",
            "booking_end_time"
        ],
        order_by="room_name asc"
    )

    # 2. Fetch Bookings for the target date using exact fieldnames
    booking_filters = {
        "booking_date": booking_date,
        "status": ["in", ["Reserved", "Completed"]]
    }
    if conference_room:
        booking_filters["conference_room"] = conference_room

    bookings = frappe.get_all(
        "Conference Booking",
        filters=booking_filters,
        fields=[
            "name",
            "booking_date",
            "conference_room",
            "meeting_title",
            "group_name",
            "client_name",
            "meeting_type",
            "booked_by",
            "projector_required",
            "full_day",
            "start_time",
            "end_time",
            "status",
            "remarks",
            "custom_no_of_attendees"
        ],
        order_by="start_time asc"
    )

    # Group bookings by room (conference_room link field)
    bookings_by_room = {}
    for b in bookings:
        b["start_time_str"] = str(b.start_time)[:5] if b.start_time else "00:00"
        b["end_time_str"] = str(b.end_time)[:5] if b.end_time else "00:00"
        b["start_time_12h"] = format_12h(b.start_time)
        b["end_time_12h"] = format_12h(b.end_time)
        bookings_by_room.setdefault(b.conference_room, []).append(b)

    # 3. Standard fallback columns
    columns = [
        {"fieldname": "room_name", "label": "Room Name", "fieldtype": "Data", "width": 160},
        {"fieldname": "capacity", "label": "Capacity", "fieldtype": "Int", "width": 90},
        {"fieldname": "has_projector", "label": "Has Projector", "fieldtype": "Check", "width": 110},
        {"fieldname": "availability_status", "label": "Status", "fieldtype": "Data", "width": 140},
        {"fieldname": "total_bookings", "label": "Total Bookings", "fieldtype": "Int", "width": 120}
    ]

    report_data = []

    for room in rooms:
        room_bookings = bookings_by_room.get(room.name, [])
        availability_status = "FREE FOR THE DAY"
        
        if room_bookings:
            availability_status = f"{len(room_bookings)} Booking(s)"

        report_data.append({
            "room_id": room.name,
            "room_name": room.room_name,
            "floor_area": room.floor_area or "",
            "capacity": room.capacity or 0,
            "has_projector": room.has_projector or 0,
            "buffer_minutes": room.buffer_minutes or 15,
            "booking_start_time": str(room.booking_start_time)[:5] if room.booking_start_time else "08:00",
            "booking_end_time": str(room.booking_end_time)[:5] if room.booking_end_time else "22:00",
            "availability_status": availability_status,
            "total_bookings": len(room_bookings),
            "bookings": room_bookings
        })

    return columns, report_data
