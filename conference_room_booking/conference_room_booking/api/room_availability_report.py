import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def get_room_availability_report(from_date=None, to_date=None, filters=None):
    """
    Room Availability Report API

    - Mobile & Web friendly
    - Date range supported
    - Availability is calculated (not stored)
    - Multi-day bookings supported
    - Future-ready for filters (capacity, projector, room, etc.)
    """

    # --------------------------------------------------
    # Normalize dates
    # --------------------------------------------------
    from_date = from_date or nowdate()
    to_date = to_date or from_date

    # --------------------------------------------------
    # Normalize future filters (safe, optional)
    # --------------------------------------------------
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    filters = filters or {}

    room_filters = {}

    #  Future filters (already supported)
    if filters.get("has_projector") is not None:
        room_filters["has_projector"] = filters.get("has_projector")

    if filters.get("conference_room"):
        room_filters["name"] = filters.get("conference_room")

    if filters.get("min_capacity"):
        room_filters["capacity"] = [">=", filters.get("min_capacity")]

    # --------------------------------------------------
    # Fetch conference rooms
    # --------------------------------------------------
    rooms = frappe.get_all(
        "Conference Room",
        filters=room_filters,
        fields=[
            "name",
            "room_name",
            "capacity",
            "has_projector",
            "buffer_minutes",
            "is_active"
        ],
        order_by="name asc"
    )

    result = []

    for room in rooms:

        # --------------------------------------------------
        # Fetch overlapping bookings (multi-day safe)
        # --------------------------------------------------
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
            as_dict=True
        )

        # --------------------------------------------------
        # Availability calculation
        # --------------------------------------------------
        if not room.is_active:
            availability = "Inactive"
        elif not bookings:
            availability = "Available"
        elif any(b.full_day for b in bookings):
            availability = "Fully Booked"
        else:
            availability = "Reserved"

        # --------------------------------------------------
        # Append response row
        # --------------------------------------------------
        result.append({
            "conference_room": room.name,
            "room_name": room.room_name,
            "capacity": room.capacity,
            "has_projector": room.has_projector,
            "buffer_minutes": room.buffer_minutes,
            "availability": availability
        })

    # --------------------------------------------------
    # Final API response
    # --------------------------------------------------
    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_rooms": len(result),
        "data": result
    }
