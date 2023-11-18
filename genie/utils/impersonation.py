
# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.www.login import _generate_temporary_login_link


@frappe.whitelist()
def generate_impersonation_url(user):
    frappe.only_for("System Manager")

    if not frappe.db.get_single_value("Genie Settings", "enable_user_impersonation"):
        frappe.throw(_("User Impersonation is disabled"))
    if user == "Administrator":
        frappe.throw(_("You cannot impersonate Administrator"))

    return _generate_temporary_login_link(user, 1)