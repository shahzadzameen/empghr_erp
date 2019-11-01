import frappe
import json
from empg_erp.utils import get_post_body,get_config_by_name,str_to_date
from datetime import datetime, timedelta
import time
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.modules.mustang.employee.employee_roster import EmployeeRoster
from empg_erp.constants.globals import ATTENDANCE_STATUS_ABSENT, ATTENDANCE_STATUS_PRESENT
from frappe import _
from erpnext.hr.utils import divide_chunks

_BODY = []
_VALID_EMPLOYEES = dict()
def add_or_update_attendance(emp_obj=dict(),obj=dict()):

    attendance_id =  frappe.db.get_value("Attendance", 
        {	
            "employee": emp_obj.get("name"),
            "attendance_date" : obj.get("attendance_date"),
            "docstatus" : 1
        },
        "name"
    )
    try:
        if attendance_id is not None:
            attendance_doc = frappe.get_doc("Attendance", attendance_id)
            new_att_doc = frappe.copy_doc(attendance_doc)
            new_att_doc.amended_from = attendance_doc.name
            attendance_doc.flags.ignore_permissions = True
            attendance_doc.cancel()
        else:
            new_att_doc = frappe.new_doc("Attendance")
            new_att_doc.employee = emp_obj.get("name") 
            new_att_doc.attendance_date = obj.get("attendance_date")

        if obj.get("status") is not None:
            new_att_doc.status = obj.get("status")	
        if obj.get("shift_start_time") is not None and obj.get("shift_start_time"):
            new_att_doc.shift_start_time = str(datetime.strptime(obj.get("shift_start_time"), '%Y-%m-%d %H:%M:%S').time())
        if obj.get("shift_end_time") is not None and obj.get("shift_end_time"):
            new_att_doc.shift_end_time = str(datetime.strptime(obj.get("shift_end_time"), '%Y-%m-%d %H:%M:%S').time())
        if obj.get("attendance_status") is not None and obj.get("attendance_status"):
            new_att_doc.attendance_status = obj.get("attendance_status")
        if (new_att_doc.check_in or new_att_doc.check_out)  and new_att_doc.status == ATTENDANCE_STATUS_ABSENT:
            new_att_doc.status = ATTENDANCE_STATUS_PRESENT	

        new_att_doc.modified_by = frappe.session.user
        new_att_doc.set_by_cron = 0
        new_att_doc.flags.ignore_permissions = True
        result = new_att_doc.save()
        new_att_doc.submit()
        return True, {
            "record":new_att_doc,
            "name":new_att_doc.name,
            "object_id":obj.get("object_id")
            } 
 
    except Exception as err:
        ErrorHandler.log_error(str(err))
        return False, str(err)

def validate_required_fields():
    _params = ["object_id","shift_start_time","shift_end_time","attendance_status","email","attendance_date"]
    _required_err = False
    _errors = []
    _invalid_employees = []
    _idx = -1
    _all_roster_statuses = dict()
    global _BODY
    global _VALID_EMPLOYEES
    _roster_mapping = get_config_by_name("ROSTER_MAPPINGS",{})
    _roster_statuses = _roster_mapping.get(frappe.session.user)
    if _roster_statuses is not None and _roster_statuses:
        for att in _BODY:
            _idx +=1
            _err = False
            for key in _params:
                if key not in att:
                    _required_err = True
                    _err = True
                    att["error"] = "{} is required.".format(key)
                    _errors.append(att)
                    break

            if _err == False:
                _err = True
                if att.get("email") not in _VALID_EMPLOYEES:
                    ''' If user is not in valid employees then get employee code by email and update valid_employees and invalid_employees'''
                    
                    if att.get("email") in _invalid_employees:
                        ''' If not employee associated with email then break current itration of loop with error'''
                        continue
                    employee_obj = frappe.db.get_value('Employee', {'user_id': att.get("email")}, ['name','employee_name','department','sub_department'],as_dict=True)

                    if employee_obj:
                        _VALID_EMPLOYEES[att.get("email")] = employee_obj
                    else:
                        _invalid_employees.append(att.get("email"))
                        att["error"] = "No Employee associated with {0}.".format(att.get("email"))
                        _errors.append(att)
                        continue
                ''' Validate shift start,end time and attendance date'''
                if att.get("shift_start_time"):
                    try:
                        time.strptime(att.get("shift_start_time"), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        att["error"] = "Invalid shift start time {0}.".format(att.get("shift_start_time"))
                        _errors.append(att)
                        continue
                
                if att.get("shift_end_time"):
                    try:
                        time.strptime(att.get("shift_end_time"), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        att["error"] = "Invalid shift end time {0}.".format(att.get("shift_end_time"))
                        _errors.append(att)
                        continue

                ''' Validate shift start,end time'''
                if att.get("shift_start_time") and att.get("shift_end_time"):
                    try:
                        if time.strptime(att.get("shift_end_time"), '%Y-%m-%d %H:%M:%S') < time.strptime(att.get("shift_start_time"), '%Y-%m-%d %H:%M:%S'):
                            att["error"] = "Shift end time must be greater than shift start time."
                            _errors.append(att)
                            continue 
                    except ValueError:
                        att["error"] = "Invalid shift start or end time {0}, {1}.".format(att.get("shift_start_time"),att.get("shift_end_time"))
                        _errors.append(att)
                        continue        

                if att.get("attendance_date"):
                    try:
                        att["attendance_date"] = datetime.strptime(att.get("attendance_date"), '%Y-%m-%d').date()
                    except ValueError:
                        att["error"] = "Invalid attendance date {0}.".format(att.get("attendance_date"))
                        _errors.append(att)
                        continue

                ''' Check attendance date is before or after cutoff date'''
                if EmployeeRoster.is_cutoff_passed(att.get("attendance_date")) == True:
                    att["error"] = "Cannot update roster on date {0}  before cutoff Date.".format(att.get("attendance_date"))
                    _errors.append(att)
                    continue
                
                ''' Check maping of roster status with attendance status'''
                _status = _roster_statuses.get(str(att.get("attendance_status")))
                if _status and _status not in _all_roster_statuses:
                    status = frappe.db.get_value("Roster Status", {"name" : _status}, "parent_status")             
                    if status is not None and status:
                        _all_roster_statuses[_status] = status
                    else:
                        att["error"] = "Roster status {0} is not linked with any Attendance Status.".format(att.get("attendance_status"))
                        _errors.append(att)
                        continue
                elif not _status:
                    att["error"] = "Roster status {0} is not linked with any Attendance Status.".format(att.get("attendance_status"))
                    _errors.append(att)
                    continue
                _BODY[_idx]["attendance_status"] = _status
                _BODY[_idx]["status"] = _all_roster_statuses[_status]
                _err = False
            if _err == True:
                _required_err = True
    else:
        _errors.append(_("Roster Statuses mapping not found."))   
    return _required_err, _errors

@frappe.whitelist()    
def sync():
    ''' Fucntion to sync other departments roster with empghr roster '''
    _max_iterations = 10000
    _errors = []
    _success = []
    _iteration = 0
    response = dict()
    global _BODY
    global _VALID_EMPLOYEES
    _BODY = get_post_body()
    ''' Get allowed user to sync attendance '''
    users = get_config_by_name("ATTENDANCE_SYNC_USERS",[])
    if frappe.session.user in users:
        if _BODY:
            validation_err,_errors =  validate_required_fields()
            if validation_err == False and len(_errors)<1:
                _chunk = divide_chunks(_BODY, 20)
                while True or _iteration <= _max_iterations:
                    try:
                        _data = next(_chunk)
                        for att in _data:
                            ''' Add or update attendance'''
                            status, result_obj = add_or_update_attendance(_VALID_EMPLOYEES[att.get("email")],att)
                            if status == False and result_obj:
                                att["error"] = result_obj
                                _errors.append(att)
                            else:
                                _success.append(result_obj)
                        _iteration += 1
                        frappe.db.commit()
                    except StopIteration:
                        break
                response = {
                    "code":200,
                    "success":_success
                }
            else:
                response = {
                    "code":201,
                    "error": _errors
                }
        return response
    else:
        return {
                "code":403,
                "error": [_("You are not allowed to sync roster/attendance.")]
            }