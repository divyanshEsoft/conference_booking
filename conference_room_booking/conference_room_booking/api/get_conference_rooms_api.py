import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_conference_rooms():
    return frappe.get_all(
        "Conference Room",
        filters={"is_active": 1},
        fields=[
            "name",
            "room_name",
            "capacity",
            "has_projector",
            "reserved_for_management",
            "buffer_minutes"
        ],
        order_by="room_name"
    )
