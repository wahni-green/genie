frappe.pages['process-flow'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Process Flow',
		single_column: true
	});
	frappe.require('process_flow.bundle.js').then(() => {
		new genie.ProcessFlow({ wrapper: page.main, page});
	})
}