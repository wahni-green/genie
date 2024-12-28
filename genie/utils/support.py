# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, flt, get_url, now
from frappe.utils.safe_exec import get_safe_globals, safe_eval
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
				**generate_ticket_details(settings),
			},
			"attachments": [hd_ticket_file] if hd_ticket_file else [],
		}
	).get("message", {}).get("name")

	return hd_ticket


def generate_ticket_details(settings):
	req_params = {}
	for row in settings.ticket_details:
		if row.type == "String":
			req_params[row.key] = row.value
		elif row.type == "Integer":
			req_params[row.key] = cint(row.value)
		elif row.type == "Context":
			req_params[row.key] = safe_eval(row.value, get_safe_globals(), {})
		else:
			req_params[row.key] = row.value

		if row.cast_to:
			if row.cast_to == "Int":
				req_params[row.key] = cint(req_params[row.key])
			elif row.cast_to == "String":
				req_params[row.key] = str(req_params[row.key])
			elif row.cast_to == "Float":
				req_params[row.key] = flt(req_params[row.key])

	return req_params


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


@frappe.whitelist()
def get_portal_url():
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}

	response = make_request(
		url=f"{settings.support_url}/api/method/frappe.auth.get_logged_user",
		headers=headers,
		payload={},
		return_response=True
	)

	sid = response.cookies.get("sid")
	return {
		"url": f"{settings.support_url}/helpdesk?sid={sid}"
	}
