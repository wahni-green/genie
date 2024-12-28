// Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.provide("genie");

genie.OpenPortal = function() {
    frappe.call({
        method: "genie.utils.support.get_portal_url",
        callback: function(r) {
            if (r.message) {
                window.open(r.message.url, "_blank");
            }
        }
    });
}