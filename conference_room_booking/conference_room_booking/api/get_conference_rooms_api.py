import frappe

@frappe.whitelist()
def get_conference_rooms():
    """
    Returns all business-relevant conference room details.
    """
    rooms =  frappe.get_all(
        "Conference Room",
        fields=[
            "name",
            "room_name",
            "floor_area",
            "capacity",
            "has_projector",
            "buffer_minutes",
            "reserved_for_management",
            "is_active",
            "remarks"
        ],
        order_by="room_name asc"
    )

    total_rooms = frappe.db.count("Conference Room")
    active_rooms = frappe.db.count("Conference Room", {"is_active": 1})

    return {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "rooms": rooms
    }


