# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd.
# For license information, please see license.txt

import frappe
import json

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
	department=None,
):
	"""Create ticket in Opero Support Portal"""
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}

	ensure_portal_user(settings, headers, user, user_fullname)

	attachments = []

	if screen_recording:
		screen_recording = f"{get_url()}{screen_recording}"

		file_data = make_request(
			url=f"{settings.support_url.rstrip('/')}/api/method/upload_file",
			headers=headers,
			payload={"file_url": screen_recording},
		).get("message")

		attachments.append(file_data)

	if file_attachment:
		file_attachment = f"{get_url()}{file_attachment}"

		file_data = make_request(
			url=f"{settings.support_url.rstrip('/')}/api/method/upload_file",
			headers=headers,
			payload={"file_url": file_attachment},
		).get("message")

		attachments.append(file_data)

	response = make_request(
		url=f"{settings.support_url.rstrip('/')}/api/method/opero.api.ticket.create_opero_ticket",
		headers=headers,
		payload={
			"doc": {
				"description": description,
				"subject": title,
				"priority": priority,
				"raised_by": user,
				"raised_by_user": user,
				"user_fullname": user_fullname,
				"customer": settings.hd_customer,
				"department": department,
				"ticket_type": "Support",
				**generate_ticket_details(settings),
			},
			"attachments": attachments,
		},
	)

	return response.get("message")


def ensure_portal_user(settings, headers, user, user_fullname):
	"""Ensure portal user exists in Opero"""

	if not user:
		return

	try:
		user_data = make_request(
			url=f"{settings.support_url.rstrip('/')}/api/method/opero.api.ticket.check_portal_user",
			headers=headers,
			payload={
				"email": user
			},
			req_type="GET",
		)

		if user_data.get("data"):
			return

	except Exception:
		pass


	make_request(
		url=f"{settings.support_url.rstrip('/')}/api/method/opero.api.ticket.create_portal_user",
		headers=headers,
		payload={
			"email": user,
			"first_name": user_fullname or user.split("@")[0],
			"enabled": 1,
			"hd_customer": settings.hd_customer,
			"roles": [
				{"role": "Opero Ticket Raiser"}
			],
		},
		req_type="POST",
	)


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
def get_portal_url(user=frappe.session.user):
	support_url = frappe.db.get_single_value("Genie Settings", "support_url")

	try:
		return {
			"url": f"{support_url}/opero/opero/account/login"
		}

	except Exception:
		frappe.log_error(
			title="Support Portal Login Error",
			message=frappe.get_traceback(),
		)

		frappe.throw(
			"Unable to log in to the support portal. Please try again later."
		)