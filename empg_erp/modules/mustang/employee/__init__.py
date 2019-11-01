import frappe
import json
from .employee_roster import EmployeeRoster
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE

# TODO : will create a schedular after complete testing
@frappe.whitelist()
def generate_monthly():

    interval = 2
    employee = None
    if "interval" in frappe.local.form_dict:
        interval = frappe.local.form_dict["interval"]
    if "employee" in frappe.local.form_dict:
        employee = frappe.local.form_dict["employee"]

    emp_roster = EmployeeRoster(interval, employee)
    return emp_roster.run()