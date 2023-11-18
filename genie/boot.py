# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def set_bootinfo(bootinfo):
    genie_settings = frappe.get_cached_doc("Genie Settings")
    bootinfo["genie_support_enabled"] = genie_settings.enable_ticket_raising
    bootinfo["genie_max_file_size"] = genie_settings.max_recording_size
    bootinfo["genie_file_type"] = 1 if genie_settings.save_recording == "Private" else 0
