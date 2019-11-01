from erpnext.hr.doctype.attendance.attendance import Attendance
from erpnext.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from erpnext.hr.doctype.leave_application.leave_application import LeaveApplication
from empg_erp.modules.mustang.attendance.employee_attendance import validate_attendance,check_leave_record_override, \
validate_override
from empg_erp.modules.mustang.leave_allocation.leave_allocation import validate_new_leaves_allocated_value_override, \
validate_period_override
from empg_erp.modules.mustang.leave_application.leave_application import validate_leave_overlap_override,  \
validate_attendance_override, update_attendance_override, cancel_attendance_override, validate_balance_leaves

from frappe.email.doctype.auto_email_report.auto_email_report import AutoEmailReport
from empg_erp.modules.mustang.email.email import get_html_table_override
from empg_erp.utils import get_site_path


site_dir = get_site_path()

if site_dir == "mustang" :

    Attendance.validate_attendance_date = validate_attendance
    Attendance.check_leave_record = check_leave_record_override
    Attendance.validate = validate_override

    LeaveAllocation.validate_new_leaves_allocated_value = validate_new_leaves_allocated_value_override
    LeaveAllocation.validate_period = validate_period_override

    LeaveApplication.validate_leave_overlap = validate_leave_overlap_override
    LeaveApplication.validate_attendance = validate_attendance_override
    LeaveApplication.update_attendance = update_attendance_override
    LeaveApplication.cancel_attendance = cancel_attendance_override
    LeaveApplication.validate_balance_leaves = validate_balance_leaves

    AutoEmailReport.get_html_table = get_html_table_override

        