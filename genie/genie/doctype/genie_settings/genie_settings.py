# Copyright (c) 2023, Wahni IT Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from genie.utils.requests import make_request


class GenieSettings(Document):
	def validate(self):
		self.validate_sp_access()

	def validate_sp_access(self):
		if not self.enable_ticket_raising:
			return

		headers = {
			"Authorization": f"token {self.get_password('support_api_token')}",
		}

		support_portal = make_request(
			url=f"{self.support_url}/api/method/frappe.utils.change_log.get_versions",
			headers=headers,
			payload={}
		).get("message")

		if not support_portal.get("helpdesk"):
			frappe.throw(_("{0} does not have Helpdesk app installed.").format(self.support_url))
