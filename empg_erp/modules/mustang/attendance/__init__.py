import frappe
import json
from .attendance_calculation import AttendanceCalculation
from empg_erp.utils import get_config_by_name, get_post_body
from os import getenv
from frappe import _

@frappe.whitelist()    
def attendance_api(attendance=[]):

    if attendance:
        body = attendance
    else:
        body = get_post_body()

    AttendanceCalculation.MIN_EARLY = get_config_by_name("MIN_EARLY", 0)
    AttendanceCalculation.MAX_LATE = get_config_by_name("MAX_LATE", 0)
    AttendanceCalculation.GRACE_MINS = get_config_by_name("GRACE_MINS", 0)
    AttendanceCalculation.EMPLOYEE_PREFIX = getenv("EMPLOYEE_PREFIX", "EMPG")

    response = list()

    if body :

        for att_data in body:
            if "user_id" in att_data:
                attendance = AttendanceCalculation(att_data["user_id"])
                response.append(attendance.add_update_attendance(att_data))
           
    return response