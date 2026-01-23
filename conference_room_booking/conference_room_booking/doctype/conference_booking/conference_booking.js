// // Copyright (c) 2026, e.Soft Techonoligies and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("Conference Booking", {
// // 	refresh(frm) {

// // 	},
// // });



// frappe.ui.form.on("Conference Booking", {
//     booking_date: trigger_availability,
//     start_time: trigger_availability,
//     end_time: trigger_availability,
//     refresh(frm) {
//         remove_availability_panel(frm);
//     }
// });

// let availability_timer = null;

// function trigger_availability(frm) {
//     if (!frm.doc.booking_date || !frm.doc.start_time || !frm.doc.end_time) {
//         return;
//     }

//     clearTimeout(availability_timer);

//     availability_timer = setTimeout(() => {
//         frappe.call({
//             method: "conference_room_booking.conference_room_booking.doctype.conference_booking.conference_booking.get_room_availability",
//             args: {
//                 booking_date: frm.doc.booking_date,
//                 start_time: frm.doc.start_time,
//                 end_time: frm.doc.end_time,
//                 booking_name: frm.doc.name
//             },
//             callback(r) {
//                 if (!r.message) return;

//                 render_availability_panel(frm, r.message);
//                 filter_conference_room_field(frm, r.message);
//             }
//         });
//     }, 300);
// }

// function remove_availability_panel(frm) {
//     if (frm.availability_wrapper) {
//         frm.availability_wrapper.remove();
//         frm.availability_wrapper = null;
//     }
// }

// function render_availability_panel(frm, data) {
//     remove_availability_panel(frm);

//     let html = `
//         <div class="room-availability" style="margin-top:15px">
//             <h5>🏢 Room Availability</h5>
//             <table class="table table-bordered">
//                 <thead>
//                     <tr>
//                         <th>Room</th>
//                         <th>Status</th>
//                         <th>Existing Bookings</th>
//                     </tr>
//                 </thead>
//                 <tbody>
//     `;

//     data.forEach(row => {
//         let color = row.status === "Available" ? "green" : "red";

//         let details = row.conflicts?.length
//             ? row.conflicts.map(
//                 c => `${c.start_time} – ${c.end_time} (${c.meeting_title || "Meeting"})`
//             ).join("<br>")
//             : "—";

//         html += `
//             <tr>
//                 <td>${row.room}</td>
//                 <td style="color:${color}; font-weight:bold">${row.status}</td>
//                 <td>${details}</td>
//             </tr>
//         `;
//     });

//     html += "</tbody></table></div>";

//     frm.availability_wrapper = $(html);
//     frm.fields_dict.conference_room.$wrapper.after(frm.availability_wrapper);
// }

// function filter_conference_room_field(frm, data) {
//     let available_rooms = data
//         .filter(r => r.status === "Available")
//         .map(r => r.room);

//     frm.set_query("conference_room", () => {
//         return {
//             filters: {
//                 name: ["in", available_rooms]
//             }
//         };
//     });

//     if (frm.doc.conference_room &&
//         !available_rooms.includes(frm.doc.conference_room)) {
//         frm.set_value("conference_room", "");
//     }
// }
