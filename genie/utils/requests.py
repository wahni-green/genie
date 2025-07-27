# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import requests
import frappe
from frappe.integrations.utils import create_request_log


def make_request(
	url,
	headers,
	payload,
	req_type="POST",
	return_response=False
    ):
	response = requests.request(
		req_type, url, json=payload, headers=headers
	)
	log_request(url, payload, response.json() if response.status_code == 200 else response.text)
	response.raise_for_status()
	if return_response:
		return response
	return response.json()


def log_request(endpoint, payload, output):
	create_request_log(
		payload,
		request_description=endpoint,
		service_name="Genie",
		output=pretty_json(output),
		status="Completed"
	)
	frappe.db.commit()


def pretty_json(obj):
	if not obj:
		return ""

	if isinstance(obj, str):
		return obj

	return frappe.as_json(obj, indent=4)
