
import frappe

@frappe.whitelist()
def get_workflows():
    workflows = frappe.get_all(
        "Workflow Visualization",
        fields=["name", "title", "description", "chart_image", "department"],
        order_by="department,name",
    )
    return workflows

@frappe.whitelist()
def get_departments():
    return frappe.get_all(
        "Processflow Department",
        fields=["name","department", "department_color"]
    )