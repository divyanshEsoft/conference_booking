import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_conference_events(start, end, filters=None):

    # Normalize filters (Calendar sends [] sometimes)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)

    if not isinstance(filters, dict):
        filters = {}

    booking_filters = {
        "booking_date": ["between", [start[:10], end[:10]]],
        "status": ["in", ["Confirmed", "Reserved"]],
    }

    if filters.get("conference_room"):
        booking_filters["conference_room"] = filters["conference_room"]

    bookings = frappe.get_all(
        "Conference Booking",
        fields=[
            "name",
            "meeting_title",
            "booking_date",
            "start_time",
            "end_time",
            "full_day"
        ],
        filters=booking_filters
    )

    events = []
    for b in bookings:
        events.append({
            "id": b.name,
            "title": b.meeting_title,
            "start": get_datetime(f"{b.booking_date} {b.start_time}"),
            "end": get_datetime(f"{b.booking_date} {b.end_time}"),
            "allDay": b.full_day
        })

    return events


@frappe.whitelist()
def get_conference_rooms():
    return frappe.get_all(
        ""

    )
