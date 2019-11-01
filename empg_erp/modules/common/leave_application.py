# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.hr.doctype.leave_application.leave_application import add_department_leaves, \
    add_block_dates, add_holidays
from empg_erp.modules.mustang.shift import get_employee_shift
from frappe.utils import cstr
from empg_erp.utils import get_auth_team_ids, get_user_role, get_employee_code,check_advance_privilege_by_name, \
   get_config_by_name 
from empg_erp.constants.globals import LINE_MANAGER, HR_USER, HR_MANAGER, ADMINISTRATOR, EMPLOYEE, LEAVE_STATUS_OPEN, \
    LEAVE_STATUS_APPROVED, LEAVE_STATUS_REJECTED, LEAVE_STATUS_CANCELLED, LEAVE_STATUS_COLOR


@frappe.whitelist()
def get_events(start, end, filters=None):
    events = []
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "company"],
                                   as_dict=True)
    if employee:
        employee, company = employee.name, employee.company
    else:
        employee = ''
        company = frappe.db.get_value("Global Defaults", None, "default_company")

    from frappe.desk.reportview import get_filters_cond
    conditions = get_filters_cond("Leave Application", filters, [])
    user_role = get_user_role()

    subordinates = get_auth_team_ids()

    if (conditions):
        conditions += " and `tabLeave Application`.employee IN (%(subordinates)s)" % {"subordinates": subordinates}
    else:
        conditions = " and `tabLeave Application`.employee IN (%(subordinates)s)" % {"subordinates": subordinates}

    add_leaves(events, start, end, conditions)

    add_block_dates(events, start, end, employee, company)
    add_holidays(events, start, end, employee, company)

    return events

def validate_leave_approver(doctype):

    reports_to = None
    if(check_advance_privilege_by_name(get_config_by_name('ADVANCE_PRIV_AUTO_APPROVE_LEAVE')) == False):
        # reports_to = ''
        reports_to_code = frappe.get_value("Employee", doctype.employee, "reports_to")
        if(reports_to_code):
            reports_to = frappe.get_value("Employee", reports_to_code, "user_id")
        dept_leave_approver = frappe.db.get_value('Department Approver', {'parent': doctype.department,'parentfield': 'leave_approvers','approver':doctype.leave_approver}, 'approver')
        hr_role = None
        if HR_MANAGER in frappe.get_roles(frappe.session.user) or HR_USER in frappe.get_roles(frappe.session.user):
            hr_role = True
        ''' Also validating HR User and HR Manager can approve leaves'''
        if(doctype.status in [LEAVE_STATUS_APPROVED, LEAVE_STATUS_REJECTED] and doctype.employee == get_employee_code()):
            frappe.throw(_("You cannot approve/reject your own leaves"))
        elif (doctype.status in [LEAVE_STATUS_APPROVED, LEAVE_STATUS_REJECTED] and doctype.employee not in get_auth_team_ids(True) and hr_role is None):
            frappe.throw(_("You cannot approve/reject this leaves"))

@frappe.whitelist()
def get_leave_status_list(islocal,employee=None):

    # Check User with Special Privillige or not
    if(check_advance_privilege_by_name(get_config_by_name('ADVANCE_PRIV_AUTO_APPROVE_LEAVE'))):
        return [LEAVE_STATUS_OPEN, LEAVE_STATUS_APPROVED, LEAVE_STATUS_REJECTED, LEAVE_STATUS_CANCELLED]
    
    if(any(x in frappe.get_roles() for x in [HR_MANAGER, HR_USER, LINE_MANAGER,ADMINISTRATOR]) and islocal != "new" ):
        if (employee is not None and employee == get_employee_code()):
            return [LEAVE_STATUS_OPEN, LEAVE_STATUS_CANCELLED]

        return [LEAVE_STATUS_OPEN, LEAVE_STATUS_APPROVED, LEAVE_STATUS_REJECTED, LEAVE_STATUS_CANCELLED]
    
    if(islocal=="new"):
        return [LEAVE_STATUS_OPEN]
    else:
        return [LEAVE_STATUS_OPEN, LEAVE_STATUS_CANCELLED]

# Override the add leaves function from leave application (Get the function definition from leave application)
def add_leaves(events, start, end, match_conditions=None):
    query = """select name, from_date, to_date, employee_name, half_day, hourly, color,
		status, employee, docstatus
		from `tabLeave Application` where
		from_date <= %(end)s and to_date >= %(start)s <= to_date
		and docstatus < 2
		and status!="Rejected" """

    if match_conditions:
        query += match_conditions

    for d in frappe.db.sql(query, {"start":start, "end": end}, as_dict=True):
        color = LEAVE_STATUS_COLOR[d.status] if d.status in LEAVE_STATUS_COLOR else "#d2f1ff"
        e = {
			"name": d.name,
			"doctype": "Leave Application",
			"from_date": d.from_date,
			"to_date": d.to_date,
			"docstatus": d.docstatus,
			"color": color,
			"title": cstr(d.employee_name) + \
				(d.half_day and _(" (Half Day)") or "") + \
				(d.hourly and _(" (Hourly)") or ""),
		}
        if e not in events:
            events.append(e)