// Copyright (c) 2026, e.Soft Techonoligies and contributors
// For license information, please see license.txt

// frappe.query_reports["Daily Conference Meetings"] = {
// 	"filters": [

// 	]
// };



frappe.query_reports["Daily Conference Meetings"] = {
    "filters": [],

    // Format status as nice colored badges
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "status") {
            let color = "";
            let bg = "";

            if (value === "Confirmed") {
                color = "#155724";     // dark green text
                bg = "#d4edda";        // light green background (only on badge)
            }
            else if (value === "Reserved") {
                color = "#856404";     // dark yellow/orange text
                bg = "#fff3cd";        // light yellow background (only on badge)
            }

            if (color) {
                return `<span style="
                    color: ${color};
                    // background: ${bg};
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-weight: 500;
                    display: inline-block;
                    min-width: 80px;
                    text-align: center;
                ">${value}</span>`;
            }
        }

        return value;
    },

    // Only improve header — no row colors
    "after_datatable_render": function (datatable) {
        setTimeout(() => {
            // Make header row look better (optional — you can remove this block if you don't want it)
            const header = datatable.wrapper.querySelector('.dt-header-row');
            if (header) {
                header.style.backgroundColor = "#e8f1ff";   // very light blue
                header.style.fontWeight = "600";
                header.style.color = "#1e3a8a";             // darker blue text
            }
        }, 100);
    }
};