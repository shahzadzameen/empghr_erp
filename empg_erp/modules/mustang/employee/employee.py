from __future__ import unicode_literals
import frappe
from frappe import _
from empg_erp.modules.mustang.leave_application.leave_application import get_leave_details, update_leave_approver
from empg_erp.modules.mustang.leave_allocation.leave_allocation import get_leave_allocation_record
from frappe.utils import datetime,flt
from empg_erp.constants.globals import EMPLOYMENT_TYPE_PERMANENT, \
CASUAL_LEAVE_TYPE, HR_USER, HR_MANAGER, ADMINISTRATOR, LINE_MANAGER
from empg_erp.utils import str_to_date,get_date_diff_in_days,unlock_doc, get_employee_code,get_config_by_name
from empg_erp.modules.mustang.attendance.employee_attendance import update_holiday_status
from six import string_types
from empg_erp.modules.mustang.employee.employee_roster import EmployeeRoster
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.modules.mustang.shift.employee_shift import assign_employee_shift
from empg_erp.modules.common import check_is_edit
from erpnext.hr.doctype.employee.employee import get_score_date

def allot_leaves(doctype,probationary=False):
    date_obj = datetime.datetime.now()
    total_days_in_year = 365
    
    joining_date = str_to_date(doctype.date_of_joining, "%Y-%m-%d")
    j_year = joining_date.year
    curr_year = conf_year = date_obj.year
    system_launching_year = get_config_by_name('SYSTEM_LAUNCH_YEAR',2019)

    if(j_year < system_launching_year):
        j_year = system_launching_year

    if probationary:
        confirmation_date = str_to_date(doctype.final_confirmation_date, "%Y-%m-%d")
        conf_year = confirmation_date.year

    while conf_year >= j_year:
        leave_period_start = year_start = str_to_date(date_obj.strftime(str(j_year)+"-01-01"), "%Y-%m-%d")
        year_end =  str_to_date(date_obj.strftime(str(j_year)+"-12-31"), "%Y-%m-%d")
        
        if(joining_date > year_start):
            leave_days = flt(total_days_in_year - get_date_diff_in_days(year_start, joining_date))
            leave_period_start = joining_date
        else:
            leave_days = total_days_in_year

        if probationary and conf_year == j_year:
            if conf_year == joining_date.year:
                leave_days = flt(get_date_diff_in_days(joining_date,confirmation_date))
            else:
                leave_days = flt(get_date_diff_in_days(year_start,confirmation_date))

        leaves = get_auto_assigned_leaves_detail(probationary)

        for leave in leaves:
            if(leave and leave.max_leaves_allowed > 0):
                alloted_leave_balance = round(flt(leave_days*leave.max_leaves_allowed)/total_days_in_year,2)
                Leave_allocation_obj = frappe.get_doc({"doctype":"Leave Allocation"})
                Leave_allocation_obj.employee = doctype.employee
                Leave_allocation_obj.leave_type = leave.name
                Leave_allocation_obj.from_date = leave_period_start
                Leave_allocation_obj.to_date = year_end
                Leave_allocation_obj.new_leaves_allocated = alloted_leave_balance
                alloted_leave_by_type = get_leave_allocation_record(doctype.employee,leave.name,leave_period_start,year_end)
                if(alloted_leave_balance>0):
                    if(not alloted_leave_by_type):
                        Leave_allocation_obj.docstatus = 1
                        Leave_allocation_obj.flags.ignore_permissions = True
                        try:
                            Leave_allocation_obj.insert()
                        except Exception as err:
                            frappe.throw(_(err))
                            ErrorHandler.log_error(str(err))
                    elif(alloted_leave_by_type and leave.prorated_on_probation):
                        if alloted_leave_by_type[0].total_leaves_allocated != alloted_leave_balance:
                            la_doc = frappe.get_doc("Leave Allocation", alloted_leave_by_type[0].name) 
                            la_doc.update({"new_leaves_allocated": alloted_leave_balance})
                            la_doc.flags.ignore_permissions = True
                            la_doc.save()

        j_year = j_year+1

def employee_leave_allocation(doctype, employee_detail):
    
    ''' Restrict leave allocation call for HR User, HR Manager and administrator'''
    if employee_detail and any(x in frappe.get_roles() for x in [LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR]) == True:

        if(doctype.employment_type == EMPLOYMENT_TYPE_PERMANENT):
            allot_leaves(doctype)
        elif (doctype.employment_type == get_config_by_name('EMPLOYMENT_TYPE_PROBATION',"Probationary")):
            allot_leaves(doctype,True)
        if doctype.holiday_list:
            update_holiday_status(doctype.holiday_list, [doctype.name])

        ''' Update leave approver if line manager changed for employee'''
        if employee_detail[2] is not None or doctype.reports_to:
            if doctype.reports_to and doctype.reports_to != employee_detail[2]:
                update_leave_approver(doctype.name,doctype.reports_to)   


def after_insert_hook(doctype, event_name):

    employee_detail = frappe.db.get_value('Employee', doctype.employee, ['department', 'job_title', 'reports_to', 'shift_type'])

    if doctype.shift_type != None:
        emp_roster = EmployeeRoster(2, doctype.employee)
        emp_roster.run()

    if employee_detail:
        employee_leave_allocation(doctype, employee_detail)
                
def before_save_hook(doctype, event_name):

    employee_detail = frappe.db.get_value('Employee', doctype.employee, ['department', 'job_title', 'reports_to', 'shift_type'])

    if employee_detail:

        employee_leave_allocation(doctype, employee_detail)

        response = check_is_edit(doctype.name)

        if employee_detail[3] is not None and employee_detail[3] != doctype.shift_type:
            assign_employee_shift(doctype.employee, doctype.shift_type)
        
        if not doctype.flags.ignore_permissions:
            # SERVER SIDE VALIDATION
            # Line manager/Employee update profile without shift type
            if response['disabled'] and 'shift_type' in response:
                doc = frappe.get_doc("Employee", doctype.name)
                doctype.shift_type = doc.shift_type
            elif response['disabled']:  # Line manager/Employee update just shift type of their reportee's
                doc = frappe.get_doc("Employee", doctype.name)
                _shift_type = doctype.shift_type
                doctype.__dict__.update(doc.__dict__)
                doctype.shift_type = _shift_type
        
  
def get_auto_assigned_leaves_detail(probationary=False):
    _filters = {
        "is_prorated": 1
    }
    if(probationary):
        _filters = {
            "prorated_on_probation": 1
        }

    leaves = frappe.db.get_all("Leave Type",
        _filters,["name","max_leaves_allowed","prorated_on_probation"]
    )
    return leaves

@frappe.whitelist()
def get_documents(employee):
    employee_documents = []
    documents = frappe.db.get_all("Employee Document",
        {
            "parent": employee,
            "parentfield": "employee_documents"
        },["title","file"])
    if(documents):
        for document in documents:
            employee_documents.append(document.title)

    return employee_documents,documents

def allocate_probationary_leaves():
    employees = frappe.get_all("Employee",filters={'status': 'Active','employment_type':get_config_by_name('EMPLOYMENT_TYPE_PROBATION',"Probationary")})
    for employee in employees:
        try:
            doc = frappe.get_doc("Employee", employee.name)
            allot_leaves(doc,True)
            print("employee:",employee.name)
            frappe.db.commit()
        except Exception as err:
            frappe.log_error(err)
            pass