// Copyright (c) 2026, e.Soft Techonoligies and contributors
// For license information, please see license.txt

frappe.query_reports["Meeting Chart"] = {
	"filters": [
		{
			"fieldname": "booking_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		}
	],
	"onload": function(report) {
		report.page.wrapper.find('.frappe-datatable').hide();
	}
};
