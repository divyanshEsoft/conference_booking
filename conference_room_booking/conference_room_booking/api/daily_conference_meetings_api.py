import frappe
from frappe.utils import nowdate

@frappe.whitelist(allow_guest=True)
# @frappe.csrf_exempt
def get_daily_meetings():
    """
    Mobile API:
    Returns all conference meetings relevant for today.
    Supports multi-day bookings.
    One booking = one row.
    """

    today = nowdate()

    meetings = frappe.db.sql(
        """
        SELECT
            name AS booking_id,
            conference_room,
            meeting_title,
            client_name,
            booked_by,
            TIME_FORMAT(start_time, '%%H:%%i') AS start_time,
            TIME_FORMAT(end_time, '%%H:%%i') AS end_time,
            booking_date AS booking_start_date,
            COALESCE(booking_end_date, booking_date) AS booking_end_date,
            full_day,
            status
        FROM `tabConference Booking`
        WHERE
            booking_date <= %(today)s
            AND COALESCE(booking_end_date, booking_date) >= %(today)s
            AND status IN ('Confirmed', 'Reserved')
        ORDER BY
            conference_room,
            start_time
        """,
        {"today": today},
        as_dict=True,
    )

    return {
        "date": today,
        "count": len(meetings),
        "meetings": meetings,
    }
