import frappe
from frappe.utils import get_datetime, now_datetime
from datetime import timedelta


@staticmethod
def auto_mark_past_bookings_as_completed():
    """
    Auto-mark Confirmed bookings as Completed
    after End Time + Buffer Time
    """
        
    now  = now_datetime()

    bookings = frappe.get_all(
        "Conference Booking",
        filters = {"status": "Confirmed"},
        fields = ["name", "booking_date", "end_time", "conference_room"],

    )

    for b in bookings:
        room = frappe.get_cached_doc("Conference Room", b.conference_room)
        buffer_minutes = room.buffer_minutes or 0
        enddt = get_datetime(f"{b.booking_date} {b.end_time}")
        enddt_with_buffer = enddt + frappe.utils.timedelta(minutes=buffer_minutes)

        if now >= enddt_with_buffer:
            frappe.db.set_value("Conference Booking", b.name, "status", "Completed" , update_modified=False
                                )
            
    frappe.db.commit()        

