# Copyright (c) 2026, e.Soft Techonoligies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ConferenceBookingSettings(Document):
    def onload(self):
        if not self.allowed_roles:
            default_roles = ["HR", "HR Manager", "Administrator", "System Manager"]
            for role in default_roles:
                self.append("allowed_roles", {"role": role})

    def before_insert(self):
        if not self.allowed_roles:
            default_roles = ["HR", "HR Manager", "Administrator", "System Manager"]
            for role in default_roles:
                self.append("allowed_roles", {"role": role})

