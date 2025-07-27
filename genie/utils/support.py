# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, flt, get_url, now
from frappe.utils.safe_exec import get_safe_globals, safe_eval
from genie.utils.requests import make_request


@frappe.whitelist()
def create_ticket(
	title,
	description,
	screen_recording=None,
	user=None,
	user_fullname=None,
	priority="Low",
	file_attachment=None,
):
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}

	attachments = []
	if screen_recording:
		screen_recording = f"{get_url()}{screen_recording}"
		hd_ticket_file = make_request(
			url=f"{settings.support_url}/api/method/upload_file",
			headers=headers,
			payload={"file_url": screen_recording}
		).get("message")
		attachments.append(hd_ticket_file)

	if file_attachment:
		file_attachment = f"{get_url()}{file_attachment}"
		file_ = make_request(
			url=f"{settings.support_url}/api/method/upload_file",
			headers=headers,
			payload={"file_url": file_attachment}
		).get("message")
		attachments.append(file_)

	hd_ticket = make_request(
		url=f"{settings.support_url}/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new",
		headers=headers,
		payload={
			"doc": {
				"description": description,
				"subject": title,
				"priority": priority,
				"raised_by": user,
				"user_fullname":user_fullname,
				"customer": settings.hd_customer,
				**generate_ticket_details(settings),
			},
			"attachments": attachments,
		}
	).get("message", {})

	# Insert into 'Support Ticket' Doctype
	if hd_ticket.get("name"):
		support_ticket = frappe.get_doc({
			"doctype": "Support Ticket",
			"title": title,
			"status": hd_ticket.get("status"),
			"priority": hd_ticket.get("priority"),
			"description": hd_ticket.get("description"),
			"raised_by": user,
			"user_fullname": user_fullname,
			"video_file": screen_recording if screen_recording else "",
			"file_attachment": file_attachment if file_attachment else "",
			"external_ticket_id": hd_ticket.get("name")  # Save external ticket ID for reference
		})
		support_ticket.insert(ignore_permissions=True)

	return hd_ticket.get("name")


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
	response = make_request(
		url=f"{settings.support_url}/api/method/login",
		headers={
			"Content-Type": "application/json",
		},
		payload={
			"usr": settings.get_password("portal_user"),
			"pwd": settings.get_password("portal_user_password"),
		},
		return_response=True
	)

	sid = response.cookies.get("sid")
	return {
		"url": f"{settings.support_url}/helpdesk?sid={sid}"
	}
