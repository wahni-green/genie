// Copyright (c) 2025, Wahni IT Solutions Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Address Fetcher", {
	refresh: function(frm) {
        if (frm.doc.status == "Pending") {
            frm.add_custom_button(__('Customers'), function() {
                frm.call("fetch_parties", {"party_type": "Customer"});
            }, __("Fetch"));
            frm.add_custom_button(__('Suppliers'), function() {
                frm.call("fetch_parties", {"party_type": "Supplier"});
            }, __("Fetch"));
            frm.add_custom_button(__('Start'), async function() {
                await frm.call("init_address_creation");
                frm.reload_doc();
            });
        }
	},
});
