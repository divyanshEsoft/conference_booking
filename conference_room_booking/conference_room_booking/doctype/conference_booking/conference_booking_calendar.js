frappe.views.calendar["Conference Booking"] = {
    get_events_method: "conference_room_booking.conference_room_booking.api.conference_calendar.get_conference_events",

    filters: [
        {
            fieldtype: "Link",
            fieldname: "conference_room",
            options: "Conference Room",
            label: "Conference Room"
        }
    ]
};



// frappe.views.calendar["Conference Booking"] = {
//     field_map: {
//         start: "start_time",
//         end: "end_time",
//         id: "name",
//         title: "meeting_title",
//         allDay: "full_day"
//     },

//     filters: [
//         {
//             fieldtype: "Link",
//             fieldname: "conference_room",
//             options: "Conference Room",
//             label: "Conference Room"
//         }
//     ],

//     get_events_method: "frappe.desk.calendar.get_events"
// };
