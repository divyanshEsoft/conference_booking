# import frappe
# from frappe.utils import nowdate

# @frappe.whitelist()
# def get_room_availability(date=None):
#     date = date or nowdate()
#     data = []

#     rooms = frappe.get_all(
#         "Conference Room",
#         filters={"is_active": 1},
#         fields=["name"]
#     )

#     for room in rooms:
#         bookings = frappe.get_all(
#             "Conference Booking",
#             filters={
#                 "conference_room": room.name,
#                 "booking_date": date,
#                 "status": ["in", ["Confirmed", "Reserved"]],
#             },
#             fields=["full_day"]
#         )

#         if not bookings:
#             availability = "Available"
#         elif any(b.full_day for b in bookings):
#             availability = "Fully Booked"
#         else:
#             availability = "Reserved"

#         data.append({
#             "conference_room": room.name,
#             "availability": availability
#         })

#     return data
