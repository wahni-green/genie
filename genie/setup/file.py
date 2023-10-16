import frappe

def create_genie_folder():
	f = frappe.new_doc("File")
	f.file_name = "Genie"
	f.is_folder = 1
	f.folder = "Home"
	f.insert(ignore_if_duplicate=True)