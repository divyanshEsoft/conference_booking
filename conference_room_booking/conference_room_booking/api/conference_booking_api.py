import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def book_conference_room(**kwargs):
    """
    Simple API to book a conference room (requires authentication)
    All validations are handled in ConferenceBooking DocType
    """
    # Validate required fields
    required_fields = ['conference_room', 'booking_date', 'start_time', 'end_time']
    for field in required_fields:
        if not kwargs.get(field):
            frappe.throw(_(f"{field} is required"))
    
    try:
        # Extract parameters
        conference_room = kwargs.get('conference_room')
        booking_date = kwargs.get('booking_date')
        booking_end_date = kwargs.get('booking_end_date') or booking_date
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        meeting_title = kwargs.get('meeting_title')
        client_name = kwargs.get('client_name')
        meeting_type = kwargs.get('meeting_type', 'Internal')
        projector_required = int(kwargs.get('projector_required', 0))
        full_day = int(kwargs.get('full_day', 0))
        remarks = kwargs.get('remarks')
        
        booking = frappe.get_doc({
            "doctype": "Conference Booking",
            "conference_room": conference_room,
            "booking_date": booking_date,
            "booking_end_date": booking_end_date,
            "start_time": start_time,
            "end_time": end_time,
            "meeting_title": meeting_title,
            "client_name": client_name,
            "meeting_type": meeting_type,
            "projector_required": projector_required,
            "full_day": full_day,
            "remarks": remarks,
            "status": "Confirmed",
            "booked_by": frappe.session.user
        })
        
        booking.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Conference room booked successfully",
            "booking_id": booking.name
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Conference Booking API Error")
        return {
            "success": False,
            "message": str(e)
        }




import frappe

@frappe.whitelist(allow_guest=True, methods=['POST'], xss_safe=True)
def debug_request(**kwargs):
    """Debug endpoint to see what's being sent"""
    return {
        "headers": dict(frappe.request.headers),
        "method": frappe.request.method,
        "args": frappe.request.args,
        "form": frappe.request.form,
        "json": frappe.request.json,
        "data": frappe.request.data.decode() if frappe.request.data else None,
        "cookies": dict(frappe.request.cookies),
        "user": frappe.session.user
    }









# import frappe

# @frappe.whitelist(allow_guest=True, methods=['POST'], xss_safe=True)
# def book_conference_room(**kwargs):
#     """
#     Simple API to book a conference room
#     All validations are handled in ConferenceBooking DocType
#     """
#     try:
#         # Extract parameters
#         conference_room = kwargs.get('conference_room')
#         booking_date = kwargs.get('booking_date')
#         booking_end_date = kwargs.get('booking_end_date') or booking_date
#         start_time = kwargs.get('start_time')
#         end_time = kwargs.get('end_time')
#         meeting_title = kwargs.get('meeting_title')
#         client_name = kwargs.get('client_name')
#         meeting_type = kwargs.get('meeting_type', 'Internal')
#         projector_required = int(kwargs.get('projector_required', 0))
#         full_day = int(kwargs.get('full_day', 0))
#         remarks = kwargs.get('remarks')
        
#         booking = frappe.get_doc({
#             "doctype": "Conference Booking",
#             "conference_room": conference_room,
#             "booking_date": booking_date,
#             "booking_end_date": booking_end_date,
#             "start_time": start_time,
#             "end_time": end_time,
#             "meeting_title": meeting_title,
#             "client_name": client_name,
#             "meeting_type": meeting_type,
#             "projector_required": projector_required,
#             "full_day": full_day,
#             "remarks": remarks,
#             "status": "Confirmed",
#             "booked_by": frappe.session.user
#         })
        
#         booking.insert(ignore_permissions=True)
#         frappe.db.commit()
        
#         return {
#             "success": True,
#             "message": "Conference room booked successfully",
#             "booking_id": booking.name
#         }
    
#     except Exception as e:
#         frappe.db.rollback()
#         return {
#             "success": False,
#             "message": str(e)
#         }

# import frappe

# @frappe.whitelist(allow_guest=True)

# def book_conference_room(
#     conference_room,
#     booking_date,
#     booking_end_date,
#     start_time,
#     end_time,
#     meeting_title=None,
#     client_name=None,
#     meeting_type="Internal",
#     projector_required=0,
#     full_day=0,
#     remarks=None
# ):
#     """
#     Simple API to book a conference room
#     All validations are handled in ConferenceBooking DocType
#     """

#     booking = frappe.get_doc({
#         "doctype": "Conference Booking",
#         "conference_room": conference_room,
#         "booking_date": booking_date,
#         "booking_end_date": booking_end_date or booking_date,
#         "start_time": start_time,
#         "end_time": end_time,
#         "meeting_title": meeting_title,
#         "client_name": client_name,
#         "meeting_type": meeting_type,
#         "projector_required": int(projector_required),
#         "full_day": int(full_day),
#         "remarks": remarks,
#         "status": "Confirmed",   # or "Reserved" if you want approval later
#         "booked_by": frappe.session.user
#     })

#     booking.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return {
#         "success": True,
#         "message": "Conference room booked successfully",
#         "booking_id": booking.name
#     }
