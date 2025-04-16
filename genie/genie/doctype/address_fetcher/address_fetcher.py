# Copyright (c) 2025, Wahni IT Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AddressFetcher(Document):
	def validate(self):
		if self.status != "Pending":
			frappe.throw(_("Save not allowed in this status"))

		self.fetch_party_gstin()

	def fetch_party_gstin(self):
		if self.status != "Pending":
			return

		for row in self.parties:
			if row.gstin:
				continue

			row.gstin = frappe.db.get_value(
				row.party_type, row.party, "gstin" 
			)

			if not row.gstin:
				frappe.msgprint(
					_("GSTIN not found for {0} {1}").format(
						row.party_type, row.party
					),
					alert=True,
				)

	@frappe.whitelist()
	def fetch_parties(self, party_type):
		frappe.only_for("System Manager")

		if self.status != "Pending":
			frappe.throw(_("Can fetch parties only when the status is Pending"))

		if party_type not in ["Customer", "Supplier"]:
			frappe.throw(_("Invalid party type"))

		party = frappe.qb.DocType(party_type)
		dynamic_link = frappe.qb.DocType("Dynamic Link")

		wo_address = (
			frappe.qb.from_(party)
			.left_join(dynamic_link)
			.on(
				(party.name == dynamic_link.link_name)
				& (dynamic_link.link_doctype == party_type)
				& (dynamic_link.parenttype == "Address")
			)
			.select(party.name, party.gstin)
			.where(dynamic_link.name.isnull())
			.where(party.gstin.isnotnull())
			.run(as_dict=True)
		)

		if not wo_address:
			frappe.msgprint(
				_("No {0} found").format(party_type),
				alert=True,
			)
			return
		
		for row in wo_address:
			self.append(
				"parties",
				{
					"party_type": party_type,
					"party": row.name,
					"gstin": row.gstin,
				},
			)

	def create_address(self):
		if self.status != "In Process":
			frappe.throw(_("Can only create address when the status is In Process"))

		if not self.parties:
			frappe.throw(_("No parties to process"))

		from india_compliance.gst_india.utils.gstin_info import get_gstin_info

		index = 0
		for row in self.parties:
			try:
				if not row.gstin:
					row.db_set("fetched", 1)
					continue

				if row.fetched:
					continue

				gstin_data = get_gstin_info(gstin=row.gstin, throw_error=False) or {}
				if not gstin_data.get("all_addresses"):
					continue
				
				address_data = gstin_data.get("all_addresses")
				primary_address = address_data.pop(0)
				self.add_address({
					"gstin": row.gstin,
					"address_title": gstin_data.get("business_name") or row.party,
					"is_primary_address": 1,
					"links": [
						{"link_doctype": row.party_type, "link_name": row.party}
					],
					**primary_address
				})
				for address in address_data:
					self.add_address({
						"gstin": row.gstin,
						"address_title": gstin_data.get("business_name") or row.party,
						"links": [
							{"link_doctype": row.party_type, "link_name": row.party}
						],
						**address
					})

				row.db_set("fetched", 1)
				index += 1
				if index % 10 == 0:
					frappe.enqueue_doc(
						self.doctype,
						self.name,
						"create_address",
						queue="long",
						enqueue_after_commit=True,
					)
					break
			except Exception:
				frappe.log_error(
					title="Address Fetcher Error for {0} {1}".format(row.party, row.gstin),
					message=frappe.get_traceback(),
				)
				continue
	
		if self.parties[-1].fetched:
			self.db_set("status", "Completed")

	def add_address(self, data):
		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_type": "Billing",
			}
		)
		address.update(data)
		address.insert(ignore_permissions=True)

	@frappe.whitelist()
	def init_address_creation(self):
		if self.status != "Pending":
			frappe.throw(_("Can only initialize address creation when the status is Pending"))

		self.db_set("status", "In Process")
		frappe.enqueue_doc(
			self.doctype,
			self.name,
			"create_address",
			queue="long",
			enqueue_after_commit=True,
		)
		frappe.msgprint(
			_("Address creation process has been initialized."),
		)
