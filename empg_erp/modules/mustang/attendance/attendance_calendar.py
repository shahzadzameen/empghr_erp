from __future__ import unicode_literals
import frappe
from erpnext.hr.doctype.attendance.attendance import add_attendance
from empg_erp.utils import get_time_diff,get_config_by_name,str_to_date,check_advance_privilege_by_name, \
get_employee_code,get_auth_team_ids,get_user_role
from empg_erp.constants.globals import CASUAL_LEAVE_TYPE,ROSTER_STATUS_OFF,HR_MANAGER,ADMINISTRATOR,LINE_MANAGER,EMPLOYEE


@frappe.whitelist()
def get_events(start, end, filters=None):
    events = []
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})

    if not employee:
        return events

    from frappe.desk.reportview import get_filters_cond
    conditions = get_filters_cond("Attendance", filters, [])

    user_role = get_user_role()
    if (user_role == LINE_MANAGER or user_role == EMPLOYEE):
        subordinates = get_auth_team_ids()
        if (conditions):
            conditions += " and `tabAttendance`.employee IN (%(subordinates)s)" % {"subordinates": subordinates}
        else:
            conditions = " and `tabAttendance`.employee IN (%(subordinates)s)" % {"subordinates": subordinates}

    add_attendance(events, start, end, conditions=conditions)
    return events
