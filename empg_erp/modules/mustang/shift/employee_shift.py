import frappe
from frappe import _
from empg_erp.empg_erp.doctype.attendance_penalties_processed.attendance_penalties_processed import AttendancePenaltiesProcessed
from datetime import datetime
import json
from erpnext.utilities.doctype.rename_tool.rename_tool import RenameFetchFromLink
from empg_erp.empg_erp.doctype.attendance_policy_associations.attendance_policy_associations import fill_associations
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.utils import unlock_doc_list, get_config_by_name, get_previous_version
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE, LINE_MANAGER_ROLES, HR_USER, HR_MANAGER, ADMINISTRATOR

class EmployeeShift():

    def __init__(self, data):

        if(len(data) > 0):

            data = data[0]

            self.date = data.get("date", None)
            self.start_time = data.get("start_time", None)
            self.end_time = data.get("end_time", None) 
            self.name = data.get("name", None) 

@frappe.whitelist()
def assign_employee_shift(employee, shift_type):

    if shift_type == None:
        return

    _today = datetime.today()
    today_date = _today.strftime("%Y-%m-%d")
    month = _today.strftime("%m")
    year = _today.strftime("%Y")

    attendace_processed = frappe.db.get_value(
        "Attendance Penalties Processed",
        filters={
            "employee": employee,
            "month": month,
            "year": year
        }
    )

    if attendace_processed != None:
        today_date = """{0}-{1}-{2}""".format(year, month, MONTHLY_ATTENDANCE_DATE)

    emp_future_leaves = frappe.db.sql("""select * from `tabLeave Application`
    					where employee = %s and (from_date >= %s OR to_date >= %s)
    					and docstatus = 1""", (employee, today_date, today_date))

    if len(emp_future_leaves) > 0:
        frappe.throw(_("You cannot add/change shift because employee have applied for future leave"))

    _df_start_time = get_config_by_name("default_shift_start_time", "09:00:00")
    _df_end_time = get_config_by_name("default_shift_end_time", "18:00:00")

    try:
        emp_attendance_list = frappe.db.sql("""
            SELECT
                att.name,
                att.attendance_date,
                IF(st.start_time IS NULL,%(start_time)s,st.start_time) as start_time,
                IF(st.end_time IS NULL,%(end_time)s,st.end_time) as end_time,
                IF(h.name IS NULL AND ch.name IS NULL AND erch.name IS NULL, "On", "Off") as attendance_status,
                IF(h.name IS NULL AND ch.name IS NULL AND erch.name IS NULL, "Absent", "Present") as status

                FROM `tabAttendance` att 
                LEFT JOIN `tabEmployee` emp
                ON att.employee = emp.name
                LEFT JOIN `tabShift Type` st
                ON st.name = %(shift_name)s
                LEFT JOIN
                `tabHoliday List` hl ON hl.name = emp.holiday_list
                LEFT JOIN
                `tabHoliday` h ON h.parent = hl.name AND h.holiday_date = att.attendance_date
                LEFT JOIN
                `tabCompany` c ON c.name = emp.company
                LEFT JOIN
                `tabHoliday List` chl ON chl.name = c.default_holiday_list
                LEFT JOIN
                `tabHoliday` ch ON ch.parent = chl.name AND ch.holiday_date = att.attendance_date
                LEFT JOIN
                `tabHoliday List` erhl ON erhl.name = st.holiday_list
                LEFT JOIN
                `tabHoliday` erch ON erch.parent = erhl.name AND erch.holiday_date = att.attendance_date

                WHERE att.attendance_date > %(today_date)s AND att.docstatus = 1 AND att.employee = %(employee)s
        
            """, {"shift_name" : shift_type,"start_time" : _df_start_time, "end_time" : _df_end_time, "employee": employee, "today_date": today_date }, 
            as_dict=True)

    except Exception as err:
        ErrorHandler.log_error(str(err))
        frappe.throw(_("did not find roster against new employee shift"))

    if len(emp_attendance_list) > 0:

        _att_list = [emp_sh["name"] for emp_sh in emp_attendance_list]

        unlock_doc_list("Attendance", _att_list)

        for attendance in emp_attendance_list:

            try:
                emp_att = frappe.get_doc("Attendance", attendance["name"])
                emp_att.shift_start_time = attendance["start_time"]
                emp_att.shift_end_time = attendance["end_time"]
                emp_att.status = attendance["status"]
                emp_att.attendance_status = attendance["attendance_status"]
                emp_att.docstatus = 1
                emp_att.save()
            except Exception as err:
                ErrorHandler.log_error(str(err))
                frappe.throw(_("There is an error while updating Attendance"))