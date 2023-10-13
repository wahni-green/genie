# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_url, now
from genie.utils.requests import make_request


@frappe.whitelist()
def create_ticket(title, description, screen_recording=None):
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}

	hd_ticket_file = None
	if screen_recording:
		screen_recording = f"{get_url()}{screen_recording}"
		hd_ticket_file = make_request(
			url=f"{settings.support_url}/api/method/upload_file",
			headers=headers,
			payload={"file_url": screen_recording}
		).get("message")

	hd_ticket = make_request(
		url=f"{settings.support_url}/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new",
		headers=headers,
		payload={
			"doc": {
				"description": description,
				"subject": title,
			},
			"attachments": [hd_ticket_file] if hd_ticket_file else [],
		}
	).get("message", {}).get("name")

	return hd_ticket


def upload_file(content):
	file_url = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": frappe.scrub(f"ST_{frappe.session.user}_{now()}.mp4"),
			"is_private": False,
			"content": content,
			"decode": True,
		}
	).save(ignore_permissions=True).file_url

	return f"{get_url()}{file_url}"
