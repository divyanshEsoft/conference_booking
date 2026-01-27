// // Copyright (c) 2026, e.Soft Techonoligies and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("Conference Booking", {
// // 	refresh(frm) {

// // 	},
// // });




// frappe.ui.form.on("Conference Booking", {
//     refresh(frm) {
//         toggle_multiday_hint(frm);
//     },

//     booking_date(frm) {
//         // Auto-set end date if empty
//         if (!frm.doc.booking_end_date) {
//             frm.set_value("booking_end_date", frm.doc.booking_date);
//         }
//         toggle_multiday_hint(frm);
//     },

//     booking_end_date(frm) {
//         // Prevent invalid date range
//         if (
//             frm.doc.booking_end_date &&
//             frm.doc.booking_date &&
//             frm.doc.booking_end_date < frm.doc.booking_date
//         ) {
//             frappe.msgprint({
//                 title: "Invalid Date Range",
//                 message: "Booking End Date cannot be before Start Date.",
//                 indicator: "red",
//             });
//             frm.set_value("booking_end_date", frm.doc.booking_date);
//             return;
//         }

//         toggle_multiday_hint(frm);
//     },
// });set_headline_alert

// function toggle_multiday_hint(frm) {
//     if (
//         frm.doc.booking_date &&
//         frm.doc.booking_end_date &&
//         frm.doc.booking_end_date > frm.doc.booking_date
//     ) {
//         frm.dashboard.set_headline_alert(
//             __(
//                 "This booking will reserve the room for <b>multiple days</b>."
//             ),
//             "blue"
//         );
//     } else {
//         frm.dashboard.clear_headline_alert();
//     }
// }



frappe.ui.form.on("Conference Booking", {
    refresh(frm) {
        // 🔒 Lock completed bookings
        if (frm.doc.status === "Completed") {
            frm.disable_form();
            return;
        }

        toggle_multiday_hint(frm);
        toggle_time_fields(frm);
    },

    booking_date(frm) {
        // 📅 Auto-set end date if empty
        if (!frm.doc.booking_end_date) {
            frm.set_value("booking_end_date", frm.doc.booking_date);
        }

        toggle_multiday_hint(frm);
    },

    booking_end_date(frm) {
        // ❌ Prevent invalid date range
        if (
            frm.doc.booking_end_date &&
            frm.doc.booking_date &&
            frm.doc.booking_end_date < frm.doc.booking_date
        ) {
            frappe.msgprint({
                title: "Invalid Date Range",
                message: "Booking End Date cannot be before Start Date.",
                indicator: "red",
            });

            frm.set_value("booking_end_date", frm.doc.booking_date);
            return;
        }

        toggle_multiday_hint(frm);
    },

    full_day(frm) {
        toggle_time_fields(frm);

        // ℹ️ Helpful hint for multi-day full-day bookings
        if (
            frm.doc.full_day &&
            frm.doc.booking_end_date > frm.doc.booking_date
        ) {
            frappe.show_alert(
                "This room will be booked for the <b>entire day</b> on all selected dates.",
                5
            );
        }
    },
});

// =====================================================
// HELPERS
// =====================================================

function toggle_multiday_hint(frm) {
    if (
        frm.doc.booking_date &&
        frm.doc.booking_end_date &&
        frm.doc.booking_end_date > frm.doc.booking_date
    ) {
        frm.dashboard.set_headline_alert(
            __("📅 This booking will reserve the room for <b>multiple days</b>."),
            "blue"
        );
    } else {
        frm.dashboard.clear_headline_alert();
    }
}

function toggle_time_fields(frm) {
    const hide_time = frm.doc.full_day === 1 || frm.doc.full_day === true;

    frm.toggle_display("start_time", !hide_time);
    frm.toggle_display("end_time", !hide_time);
}
