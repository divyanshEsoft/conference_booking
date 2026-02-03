import frappe
from frappe.exceptions import ValidationError, PermissionError

@frappe.whitelist(allow_guest=True)
def book_conference_room(**data):
    """
    Mobile-safe API.
    ALL validations handled by Conference Booking DocType.
    """

    if frappe.session.user == "Guest":
        return {
            "success": False,
            "error_type": "AUTH",
            "message": "Session expired. Please login again."
        }

    required_fields = [
        "conference_room",
        "booking_date",
        "start_time",
        "end_time",
        "client_name",
        "meeting_type"
    ]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return {
            "success": False,
            "error_type": "VALIDATION",
            "missing_fields": missing
        }

    try:
        booking = frappe.get_doc({
            "doctype": "Conference Booking",
            "conference_room": data["conference_room"],
            "booking_date": data["booking_date"],
            "booking_end_date": data.get("booking_end_date") or data["booking_date"],
            "start_time": data["start_time"],
            "end_time": data["end_time"],
            "meeting_title": data.get("meeting_title"),
            "group_name": data.get("group_name"),
            "client_name": data["client_name"],
            "meeting_type": data["meeting_type"],
            "projector_required": 1 if str(data.get("projector_required", 0)) in ("1", "true", "True") else 0,
            "full_day": 1 if str(data.get("full_day", 0)) in ("1", "true", "True") else 0,
            "remarks": data.get("remarks"),
            "status": data.get("status", "Reserved"),
            "booked_by": frappe.session.user
        })

        booking.insert(ignore_permissions=True)

        return {
            "success": True,
            "booking_id": booking.name,
            "status": booking.status,
            "starts_on": booking.starts_on,
            "ends_on": booking.ends_on
        }

    # 🔹 All business-rule failures (frappe.throw)
    except ValidationError as e:
        frappe.db.rollback()
        return {
            "success": False,
            "error_type": "VALIDATION",
            "message": str(e)
        }

    # 🔹 Permission / role issues
    except PermissionError as e:
        frappe.db.rollback()
        return {
            "success": False,
            "error_type": "PERMISSION",
            "message": str(e)
        }

    # 🔹 Any other business exception from DocType
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Conference Booking API Error")
        return {
            "success": False,
            "error_type": "SERVER",
            "message": str(e) if frappe.conf.developer_mode else "Unable to book conference room"
        }







# import frappe
# from frappe.utils import getdate, get_datetime

# @frappe.whitelist(allow_guest=True)
# # @frappe.csrf_exempt
# def book_conference_room(**data):
#     try:
#         # -----------------------------
#         # 1️⃣ Required Fields
#         # -----------------------------
#         required_fields = [
#             "conference_room",
#             "booking_date",
#             "start_time",
#             "end_time",
#             "client_name",
#             "meeting_type"
#         ]

#         for field in required_fields:
#             if not data.get(field):
#                 return error_response(f"Missing required field: {field}")

#         booking_date = getdate(data["booking_date"])
#         booking_end_date = getdate(data.get("booking_end_date") or booking_date)

#         start_time = data["start_time"]
#         end_time = data["end_time"]

#         if start_time >= end_time:
#             return error_response("End time must be after start time")

#         # -----------------------------
#         # 2️⃣ Validate Room
#         # -----------------------------
#         room = frappe.db.get_value(
#             "Conference Room",
#             data["conference_room"],
#             ["name", "is_active"],
#             as_dict=True
#         )

#         if not room:
#             return error_response("Conference room not found")

#         if not room.is_active:
#             return error_response("Conference room is inactive")

#         # -----------------------------
#         # 3️⃣ Overlap Check (CORE LOGIC)
#         # -----------------------------
#         conflict = frappe.db.sql(
#             """
#             SELECT name
#             FROM `tabConference Booking`
#             WHERE
#                 conference_room = %(room)s
#                 AND status IN ('Confirmed', 'Reserved')
#                 AND booking_date <= %(end_date)s
#                 AND COALESCE(booking_end_date, booking_date) >= %(start_date)s
#                 AND (
#                     start_time < %(end_time)s
#                     AND end_time > %(start_time)s
#                 )
#             LIMIT 1
#             """,
#             {
#                 "room": data["conference_room"],
#                 "start_date": booking_date,
#                 "end_date": booking_end_date,
#                 "start_time": start_time,
#                 "end_time": end_time,
#             },
#         )

#         if conflict:
#             return error_response("Conference room already booked for this time slot")

#         # -----------------------------
#         # 4️⃣ Create Booking
#         # -----------------------------
#         booking = frappe.new_doc("Conference Booking")
#         booking.conference_room = data["conference_room"]
#         booking.booking_date = booking_date
#         booking.booking_end_date = booking_end_date
#         booking.start_time = start_time
#         booking.end_time = end_time
#         booking.meeting_title = data.get("meeting_title")
#         booking.client_name = data["client_name"]
#         booking.meeting_type = data["meeting_type"]
#         booking.projector_required = data.get("projector_required", 0)
#         booking.status = "Reserved"
#         booking.booked_by = frappe.session.user if frappe.session.user != "Guest" else None

#         booking.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "booking_id": booking.name,
#             "message": "Conference room booked successfully"
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Conference Room Booking API Error")
#         return error_response("Something went wrong while booking")


# def error_response(message):
#     return {
#         "status": "error",
#         "message": message
#     }











# import frappe

# @frappe.whitelist(methods=["POST"])
# def book_room(**data):

#     if frappe.session.user == "Guest":
#         return {
#             "success": False,
#             "message": "Invalid or expired session"
#         }

#     data.pop("booked_by", None)

#     booking = frappe.get_doc({
#         "doctype": "Conference Booking",
#         "conference_room": data["conference_room"],
#         "booking_date": data["booking_date"],
#         "booking_end_date": data.get("booking_end_date") or data["booking_date"],
#         "start_time": data["start_time"],
#         "end_time": data["end_time"],
#         "meeting_type": data["meeting_type"],
#         "client_name": data["client_name"],
#         "status": "Confirmed",
#         "booked_by": frappe.session.user
#     })

#     booking.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return {
#         "success": True,
#         "booking_id": booking.name
#     }


# # import frappe
# # from frappe import _
# # from frappe.exceptions import (
# #     ValidationError,
# #     PermissionError,
# #     DoesNotExistError
# # )

# # @frappe.whitelist(allow_guest=True)
# # @frappe.csrf_exempt
# # def book_conference_room(**kwargs):
# #     """
# #     Mobile-safe API to book a conference room.
# #     Authentication via SID or API Token.
# #     Returns clean, structured responses for ALL failures.
# #     """

# #     # --------------------------------------------
# #     # 1️⃣ AUTH CHECK (SID / TOKEN)
# #     # --------------------------------------------
# #     if frappe.session.user == "Guest":
# #         return {
# #             "success": False,
# #             "error_type": "AUTH",
# #             "message": "Session expired or user not logged in. Please login again."
# #         }

# #     try:
# #         # --------------------------------------------
# #         # 2️⃣ REQUIRED FIELDS CHECK (API LEVEL)
# #         # --------------------------------------------
# #         required_fields = [
# #             "conference_room",
# #             "booking_date",
# #             "start_time",
# #             "end_time",
# #             "meeting_type",
# #             "client_name"
# #         ]

# #         missing_fields = [
# #             field for field in required_fields if not kwargs.get(field)
# #         ]

# #         if missing_fields:
# #             return {
# #                 "success": False,
# #                 "error_type": "VALIDATION",
# #                 "message": "Missing required fields",
# #                 "missing_fields": missing_fields
# #             }

# #         # --------------------------------------------
# #         # 3️⃣ CREATE CONFERENCE BOOKING DOC
# #         # --------------------------------------------
# #         booking = frappe.get_doc({
# #             "doctype": "Conference Booking",
# #             "conference_room": kwargs.get("conference_room"),
# #             "booking_date": kwargs.get("booking_date"),
# #             "booking_end_date": kwargs.get("booking_end_date") or kwargs.get("booking_date"),
# #             "start_time": kwargs.get("start_time"),
# #             "end_time": kwargs.get("end_time"),
# #             "meeting_title": kwargs.get("meeting_title"),
# #             "client_name": kwargs.get("client_name"),
# #             "meeting_type": kwargs.get("meeting_type"),
# #             "projector_required": int(kwargs.get("projector_required", 0)),
# #             "full_day": int(kwargs.get("full_day", 0)),
# #             "remarks": kwargs.get("remarks"),
# #             "status": "Confirmed",
# #             "booked_by": frappe.session.user
# #         })

# #         # --------------------------------------------
# #         # 4️⃣ INSERT (ALL BUSINESS RULES RUN HERE)
# #         # --------------------------------------------
# #         booking.insert(ignore_permissions=True)
# #         frappe.db.commit()

# #         # --------------------------------------------
# #         # 5️⃣ SUCCESS RESPONSE
# #         # --------------------------------------------
# #         return {
# #             "success": True,
# #             "message": "Conference room booked successfully",
# #             "booking_id": booking.name,
# #             "booked_by": frappe.session.user,
# #             "conference_room": booking.conference_room,
# #             "booking_date": booking.booking_date,
# #             "start_time": booking.start_time,
# #             "end_time": booking.end_time
# #         }

# #     # --------------------------------------------
# #     # 6️⃣ HANDLED / EXPECTED ERRORS
# #     # --------------------------------------------
# #     except ValidationError as e:
# #         frappe.db.rollback()
# #         return {
# #             "success": False,
# #             "error_type": "VALIDATION",
# #             "message": str(e)
# #         }

# #     except PermissionError as e:
# #         frappe.db.rollback()
# #         return {
# #             "success": False,
# #             "error_type": "PERMISSION",
# #             "message": str(e)
# #         }

# #     except DoesNotExistError as e:
# #         frappe.db.rollback()
# #         return {
# #             "success": False,
# #             "error_type": "NOT_FOUND",
# #             "message": "Conference Room does not exist"
# #         }

# #     # --------------------------------------------
# #     # 7️⃣ UNEXPECTED / SYSTEM ERRORS
# #     # --------------------------------------------
# #     except Exception as e:
# #         frappe.db.rollback()
# #         frappe.log_error(
# #             frappe.get_traceback(),
# #             "Conference Room Booking API Error"
# #         )
# #         return {
# #             "success": False,
# #             "error_type": "SERVER_ERROR",
# #             "message": "Something went wrong while booking the conference room"
# #         }






# # import frappe

# # @frappe.whitelist(allow_guest=True, methods=['POST'], xss_safe=True)
# # def book_conference_room(**kwargs):
# #     """
# #     Simple API to book a conference room
# #     All validations are handled in ConferenceBooking DocType
# #     """
# #     try:
# #         # Extract parameters
# #         conference_room = kwargs.get('conference_room')
# #         booking_date = kwargs.get('booking_date')
# #         booking_end_date = kwargs.get('booking_end_date') or booking_date
# #         start_time = kwargs.get('start_time')
# #         end_time = kwargs.get('end_time')
# #         meeting_title = kwargs.get('meeting_title')
# #         client_name = kwargs.get('client_name')
# #         meeting_type = kwargs.get('meeting_type', 'Internal')
# #         projector_required = int(kwargs.get('projector_required', 0))
# #         full_day = int(kwargs.get('full_day', 0))
# #         remarks = kwargs.get('remarks')
        
# #         booking = frappe.get_doc({
# #             "doctype": "Conference Booking",
# #             "conference_room": conference_room,
# #             "booking_date": booking_date,
# #             "booking_end_date": booking_end_date,
# #             "start_time": start_time,
# #             "end_time": end_time,
# #             "meeting_title": meeting_title,
# #             "client_name": client_name,
# #             "meeting_type": meeting_type,
# #             "projector_required": projector_required,
# #             "full_day": full_day,
# #             "remarks": remarks,
# #             "status": "Confirmed",
# #             "booked_by": frappe.session.user
# #         })
        
# #         booking.insert(ignore_permissions=True)
# #         frappe.db.commit()
        
# #         return {
# #             "success": True,
# #             "message": "Conference room booked successfully",
# #             "booking_id": booking.name
# #         }
    
# #     except Exception as e:
# #         frappe.db.rollback()
# #         return {
# #             "success": False,
# #             "message": str(e)
# #         }

# # import frappe

# # @frappe.whitelist(allow_guest=True)

# # def book_conference_room(
# #     conference_room,
# #     booking_date,
# #     booking_end_date,
# #     start_time,
# #     end_time,
# #     meeting_title=None,
# #     client_name=None,
# #     meeting_type="Internal",
# #     projector_required=0,
# #     full_day=0,
# #     remarks=None
# # ):
# #     """
# #     Simple API to book a conference room
# #     All validations are handled in ConferenceBooking DocType
# #     """

# #     booking = frappe.get_doc({
# #         "doctype": "Conference Booking",
# #         "conference_room": conference_room,
# #         "booking_date": booking_date,
# #         "booking_end_date": booking_end_date or booking_date,
# #         "start_time": start_time,
# #         "end_time": end_time,
# #         "meeting_title": meeting_title,
# #         "client_name": client_name,
# #         "meeting_type": meeting_type,
# #         "projector_required": int(projector_required),
# #         "full_day": int(full_day),
# #         "remarks": remarks,
# #         "status": "Confirmed",   # or "Reserved" if you want approval later
# #         "booked_by": frappe.session.user
# #     })

# #     booking.insert(ignore_permissions=True)
# #     frappe.db.commit()

# #     return {
# #         "success": True,
# #         "message": "Conference room booked successfully",
# #         "booking_id": booking.name
# #     }
