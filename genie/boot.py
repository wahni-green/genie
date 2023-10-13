# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def set_bootinfo(bootinfo):
    bootinfo["genie_support_enabled"] = frappe.db.get_single_value(
        "Genie Settings", "enable_ticket_raising", cache=True
    )
