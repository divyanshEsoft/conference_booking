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
		// Force ignore prepared_report so Meeting Chart always runs live.
		report.ignore_prepared_report = true;

		report.page.wrapper.find('.frappe-datatable').hide();
	}
};
