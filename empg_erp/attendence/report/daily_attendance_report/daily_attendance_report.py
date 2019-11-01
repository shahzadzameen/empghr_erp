# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime,time, timedelta
from empg_erp.modules.mustang.employee.employee_roster import EmployeeRoster
import json
from pypika import Query, Tables, Field, JoinType, functions as fn, Case, Order
from empg_erp.utils import get_limit_from_filters, \
    get_page_count, path_child, unlock_doc, get_time_diff, check_advance_privilege_by_name, get_config_by_name, \
    get_user_filters_by_role, get_auth_team_ids,get_employee_code,get_user_role, get_timestamp,get_formatted_hours
from empg_erp.modules.mustang.shift import get_employee_shift
from empg_erp.modules.mustang.attendance.employee_attendance import checking_attandence_processed
from empg_erp.constants.globals import PAGE_SIZE, ATTENDANCE_MANAGER, HR_MANAGER,ADMINISTRATOR,EMPLOYEE, LINE_MANAGER, HR_USER
from frappe.utils.background_jobs import enqueue

empatt, tabEmp, ats, le = Tables(
    'tabAttendance','tabEmployee', 'tabRoster Status', 'tabLeave Application'
)

def get_list(filters, return_count = False, export = False):
    
    if "page" in filters:
        page = filters["page"]
        concat = str(page).split('_')
        limit = str(concat[0])
    else:
        limit = str(PAGE_SIZE)


    query_obj = Query.from_(empatt)\
            .join(tabEmp, how=JoinType.inner)\
            .on_field("employee")\
            .join(ats, how=JoinType.left)\
            .on(ats.name == empatt.attendance_status)\
            .join(le, how=JoinType.left)\
            .on((le.employee == empatt.employee) & (le.docstatus < 2) & (empatt.attendance_date[le.from_date:le.to_date]))\
            .where(empatt.docstatus == 1).groupby( empatt.employee, empatt.attendance_date)\
            .orderby(empatt.attendance_date, order=Order.desc)
    
    if return_count == False:
        if export == True:
            query_obj = query_obj.select(
                empatt.name,
                empatt.company,
                (le.status).as_("leave_status"),
                tabEmp.department,
                tabEmp.sub_department,
                tabEmp.job_title,
                tabEmp.date_of_joining,
                tabEmp.employment_type,
                tabEmp.reports_to,
                tabEmp.office_region,
                tabEmp.office_sub_region,
                tabEmp.office_city,
                tabEmp.status,
                tabEmp.company,
                tabEmp.department,
                empatt.attendance_request,
                empatt.attendance_date,
                empatt.employee,
                empatt.empghr_employee_attendance_pull_id,
                empatt.attendance_status,
                empatt.shift_start_time,
                empatt.shift_end_time,
                (ats.name).as_("status_name"),
                Case().when(empatt.employee_name.isnull(), "-").else_(empatt.employee_name).as_("employee_name"),\
                Case().when(
                        le.leave_type.isnull() & empatt.check_out.isnull() & empatt.check_in.isnull() & empatt.attendance_status == 'On',
                        "Not Applied"
                    ).else_(
                        Case().when(
                            fn.Count(le.leave_type) > 1, "Multiple Leaves Applied"
                        ).else_(
                            le.leave_type
                        )
                    ).as_("leave_type"),\
                Case().when(empatt.check_out.isnull() , "-").else_(fn.Cast(empatt.check_out, "time")).as_("check_out"),\
                Case().when(empatt.check_in.isnull() , "-").else_(fn.Cast(empatt.check_in, "time")).as_("check_in"),\
                Case().when((empatt.late_arrival.isnull()) | (empatt.late_arrival <= 0), "-").else_(empatt.late_arrival).as_("late_arrival"),\
                Case().when((empatt.left_early.isnull()) | (empatt.left_early <= 0), "-").else_(empatt.left_early).as_("left_early"),\
                Case().when(empatt.working_hours.isnull(), "-").else_(empatt.working_hours).as_("working_hours"),\
                Case().when(ats.color.isnull(),'#428b46').else_(ats.color).as_("color")
                
            ).limit(limit)
        else:
            query_obj = query_obj.select(
            empatt.name,
            empatt.company,
            (le.status).as_("leave_status"),
            tabEmp.department,
            empatt.attendance_request,
            empatt.attendance_date,
            empatt.employee,
            empatt.empghr_employee_attendance_pull_id,
            empatt.attendance_status,
            empatt.shift_start_time,
            empatt.shift_end_time,
            (ats.name).as_("status_name"),
            Case().when(empatt.employee_name.isnull(), "-").else_(empatt.employee_name).as_("employee_name"),\
            Case().when(
                    le.leave_type.isnull() & empatt.check_out.isnull() & empatt.check_in.isnull() & empatt.attendance_status == 'On',
                    "Not Applied"
                ).else_(
                    Case().when(
                        fn.Count(le.leave_type) > 1, "Multiple Leaves Applied"
                    ).else_(
                        le.leave_type
                    )
                ).as_("leave_type"),\
            Case().when(empatt.check_out.isnull() , "-").else_(fn.Cast(empatt.check_out, "time")).as_("check_out"),\
            Case().when(empatt.check_in.isnull() , "-").else_(fn.Cast(empatt.check_in, "time")).as_("check_in"),\
            Case().when((empatt.late_arrival.isnull()) | (empatt.late_arrival <= 0), "-").else_(empatt.late_arrival).as_("late_arrival"),\
            Case().when((empatt.left_early.isnull()) | (empatt.left_early <= 0), "-").else_(empatt.left_early).as_("left_early"),\
            Case().when(empatt.working_hours.isnull(), "-").else_(empatt.working_hours).as_("working_hours"),\
            Case().when(ats.color.isnull(),'#428b46').else_(ats.color).as_("color")
            
        ).limit(limit)

    else:

        query_obj = query_obj.select(
            fn.Count(0)
        )

    query_obj = get_condition(filters, query_obj)
    
    if return_count == True:

        query_obj = Query.from_(query_obj).select((fn.Count(0)).as_("total"))

    try:
        employee_data = frappe.db.sql(query_obj.get_sql(quote_char="`"), as_dict=True)
        return employee_data

    except:
        return []

def prepare_report_data(att_list, limit):

    columns, data = [], []

    _show_checkbox = any(x in frappe.get_roles() for x in [ATTENDANCE_MANAGER, LINE_MANAGER,ADMINISTRATOR]) == True

    for att in att_list:
        _data = list()

        if _show_checkbox:
            _data.append(update_actions(att.name, att.shift_start_time, att.shift_end_time,str(att.employee),
                                      att.attendance_status, att.attendance_date))
        _data.append(att.employee)
        _data.append(att.employee_name)
        _data.append(att.attendance_date)
        _data.append(datetime.strftime(att.attendance_date, "%a"))
        attendance_status = ''
        if (att.attendance_status is not None):
            attendance_status = """<div class='text-left'><span class='indicators-shift' style='background-color:{1}'></span>{0}</div>""".format(
                att.attendance_status,
                att.color)
        _data.append(attendance_status)
        _data.append(att.check_in)
        _data.append(att.check_out)
        if att.late_arrival is not None:
            if att.late_arrival != '-':
                att.late_arrival = int(float(att.late_arrival))
        _data.append(att.late_arrival)
        if att.left_early is not None:
            if att.left_early != '-':
                att.left_early = int(float(att.left_early))
        _data.append(att.left_early)
        if att.working_hours != '-':
            att.working_hours = get_formatted_hours(att.working_hours)
        _data.append((att.working_hours))
        leave_type = '-'
        if att.leave_type is not None:
            if att.leave_type != 'Multiple Leaves Applied' and att.leave_status is not None:
                leave_type = "{0}-{1}".format(att.leave_status,att.leave_type)
            else:
                leave_type = att.leave_type


        _data.append(leave_type)
        _data.append(get_action_input(att.name, att.shift_start_time, att.shift_end_time,str(att.employee),
                                      att.attendance_status, att.attendance_date))

        data.append(_data)
    edit_all = _("<input type='checkbox'  class='selectall' name='select_all' onclick='select_all_checkbox(this," + '10037' + ")'> </input>""")+ "::55"

    columns = [
        _("Code<input type='hidden' value='" + limit + "' id='page' />") + "::110", _("Employee") + "::180",
        _("Date") + ":Date:100", _("Day") + "::40", _("Shift") + "::100",
        _("Checkin-Time") + "::10", _("Checkout-Time") + "::10", _("Arrived Late By(mins)") + "::10",
        _("Left Early By(mins)") + "::10", _("Working Hours") + "::40", _("Leave Status") + "::160", _("Action") + "::5"
    ]
    if _show_checkbox:
        columns.insert(0, edit_all)

    return columns, data

def prepare_excel_data(att_list):

    columns, data = [], []

    for att in att_list:
        
        _data = list()

        _data.append(att.employee)
        _data.append(att.employee_name)
        _data.append(att.job_title)
        _data.append(att.sub_department)
        _data.append(att.date_of_joining)
        _data.append(att.employment_type)
        _data.append(att.reports_to)
        _data.append(att.office_region)
        _data.append(att.office_sub_region)
        _data.append(att.office_city)
        _data.append(att.status)
        _data.append(att.company)
        leave_type = '-'
        leave_status = '-'
        if att.leave_type is not None:
            leave_status = att.leave_status
            leave_type = att.leave_type

        _data.append(leave_type)
        _data.append(leave_status)
        _data.append(att.attendance_date)
        _data.append(datetime.strftime(att.attendance_date, "%a"))
        _data.append(att.shift_start_time),
        _data.append(att.shift_end_time),
        _data.append(att.attendance_status)
        _data.append(att.check_in)
        _data.append(att.check_out)
        if att.late_arrival is not None:
            if att.late_arrival != '-':
                att.late_arrival = int(att.late_arrival)
        _data.append(att.late_arrival)

        data.append(_data)
        
    columns = [
        _("Employee") + "::100", _("Employee Name") + "::180",
        _("Job Title") + "::100", _("Sub Department") + "::100",
        _("DOJ") + "::10", _("Employment Type") + "::10", _("Reports To") + "::10",
        _("Office Region") + "::10", _("Office Sub Region") + "::40", _("Office City") + "::160",
        _("Status") + "::10", _("Company") + "::40", _("leave_type") + "::160",
        _("Leave Status") + "::10", _("attendance_date") + ":Date:100", _("Day") + "::10",
         _("Shift Start") + "::10", _("Shift End") + "::10", _("Roster") + "::20",
        _("Checkin-Time") + "::10", _("Checkout-Time") + "::10", _("Arrived Late By(mins)") + "::10",
    ]

    return columns, data
    

def execute(filters=None):

    limit = str(PAGE_SIZE)
    if "page" in filters:
        limit = filters["page"]

    # validate if its an employee then user filter must be 'Me'

    if not (any(x in frappe.get_roles() for x in [HR_MANAGER, HR_USER, ADMINISTRATOR])):
        if get_user_role() == EMPLOYEE:
           if filters.get("user") != 'Me':
               filters["user"] = 'Me'

    if "is_excel" in filters and filters["is_excel"] == True:
        att_list = get_list(filters,False,True)
        return prepare_excel_data(att_list)
    else:
        att_list = get_list(filters)
        return prepare_report_data(att_list, limit)


def update_actions(id, shift_start_time, shift_end_time, employee, attendance_status, attendance_date):

    action_disabled = "<input type='checkbox' class='individual' name='emp_action_check' " + 'disabled' + "  value=" + id + "  id=" + employee + ">"

    if employee is not None:
        if employee == get_employee_code():
            return action_disabled
    editBtn = action_disabled
    AuthRole = frappe.get_roles(frappe.session.user)
    today_date = str(datetime.strftime(datetime.today(), '%Y-%m-%d'))

    allowed_roles = [ATTENDANCE_MANAGER, HR_MANAGER, ADMINISTRATOR, LINE_MANAGER, HR_USER]

    if ATTENDANCE_MANAGER in AuthRole:
        editBtn = "<input type='checkbox' class='individual' name='emp_action_check[]'  value=" + id + "  id=" + employee + ">"
    elif len(list(set(allowed_roles) & set(AuthRole))) > 0 and EmployeeRoster.is_cutoff_passed(
            attendance_date) == False:
        editBtn = "<input type='checkbox' class='individual' name='emp_action_check[]' value=" + id + "  id=" + employee + ">"
    else:
        editBtn = action_disabled

    return editBtn


def get_condition(filters, query_obj):

    AuthRole = frappe.get_roles(frappe.session.user)
    # if user filter has not assigned on page load and its not 'Administrator' then assign 'Me' by default
    if filters.get("user") is None and ADMINISTRATOR not in AuthRole:
        user, default_user_filter = get_user_filters_by_role()
        filters["user"] = default_user_filter

    if filters.get("employee"):
        query_obj = query_obj.where(empatt.employee == filters.get("employee"))
    
    if filters.get("department"):
        query_obj = query_obj.where(tabEmp.department == filters.get("department"))
    if filters.get("sub_department"):
        query_obj = query_obj.where(tabEmp.sub_department == filters.get("sub_department"))
    if filters.get("from_date"):
        query_obj = query_obj.where(empatt.attendance_date >= str(datetime.strptime((filters.get("from_date")), '%Y-%m-%d %H:%M:%S').date()))
        
        check_in_time = datetime.strptime((filters.get("from_date")), '%Y-%m-%d %H:%M:%S').time()
        if check_in_time != time(0, 0):
            query_obj = query_obj.where(fn.Cast(empatt.check_in, "time") >= str(check_in_time))
    
    if filters.get("to_date"):
        query_obj = query_obj.where(empatt.attendance_date <= str(datetime.strptime((filters.get("to_date")), '%Y-%m-%d %H:%M:%S').date()))

        check_out_time = datetime.strptime((filters.get("to_date")), '%Y-%m-%d %H:%M:%S').time()
        if check_out_time != time(0, 0):
            query_obj = query_obj.where(fn.Cast(empatt.check_out, "time") <= str(check_out_time))

    if filters.get("company"):
        query_obj = query_obj.where(empatt.company == filters.get("company"))

    if filters.get("late_arrival"):
        query_obj = query_obj.where(empatt.late_arrival == filters.get("late_arrival"))

    if filters.get("left_early"):
        query_obj = query_obj.where(empatt.left_early == filters.get("left_early"))

    if filters.get("user"):
        if filters.get("user") == "Me":
            userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
            if userId is not None:
                query_obj = query_obj.where(empatt.employee == userId)

        if filters.get("user") == "Employee Reporting To Me":
            userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
            if userId is not None:
                query_obj = query_obj.where(tabEmp.reports_to == userId)

        if filters.get("user") == "All Team":
            AuthRole = frappe.get_roles(frappe.session.user)
            # if it is HR manager,All tabEmp attendance shown to him as per old hrms
            if HR_MANAGER not in AuthRole:
                employee_list = get_auth_team_ids(returnList=True)
                if employee_list != "":
                    query_obj = query_obj.where(empatt.employee.isin(employee_list))

    return query_obj


def get_action_input(id, shift_start_time, shift_end_time, employee, attendance_status, attendance_date):

    att_req_btn = """<a  href="#Form/Attendance%20Request/New%20Attendance%20Request%201?employee={0}&attendance_date={1}" target="_blank" title="Attendance Request"><i class="fa fa-calendar-check-o"></i></a>""".format(employee,attendance_date)
    if employee is not None:
        if employee == get_employee_code():
            if(EmployeeRoster.is_cutoff_passed(attendance_date) == False):
                return att_req_btn
            return '-'
    editBtn = '-'
    AuthRole = frappe.get_roles(frappe.session.user)
    today_date = str(datetime.strftime(datetime.today(), '%Y-%m-%d'))

    allowed_roles = [ATTENDANCE_MANAGER, HR_MANAGER, ADMINISTRATOR, LINE_MANAGER, HR_USER ]
    
    if ATTENDANCE_MANAGER in AuthRole:
        editBtn = """<a  href="#Form/Attendance/{0}" target="_blank"><i class="fa fa-edit"></i></a>
                    """.format(id)
    elif len(list(set(allowed_roles) & set(AuthRole))) > 0 and EmployeeRoster.is_cutoff_passed(attendance_date) == False:
        editBtn = """<a href="javascript:;" onclick="attendance_report_action(this, '{0}', '{1}', '{2}', '{3}')"><i class="fa fa-edit"></i></a>
                            """.format(id, shift_start_time, shift_end_time, attendance_status)

    if(EmployeeRoster.is_cutoff_passed(attendance_date) == False):
        if editBtn == '-':
            editBtn = ''
        editBtn = """{0} {1}""".format(editBtn,att_req_btn)
    return editBtn


@frappe.whitelist()
def get_count(filters={}):

    att_count = get_list(json.loads(filters),True)
    total_records = 0

    if len(att_count) > 0:
        total_records = att_count[0]["total"]

    user, default_user_filter = get_user_filters_by_role()

    return {'user': user, 'default_user_filter': default_user_filter,
            'pagination': get_page_count(total_records, PAGE_SIZE), 'totalRecords': total_records}


@frappe.whitelist()
def update_attendance_time(data):

    if (not any(x in frappe.get_roles() for x in [LINE_MANAGER,ATTENDANCE_MANAGER,ADMINISTRATOR])):    
        return {"code": 400, "err": _("You dont have enough privileges to update roster")}

    att_data = json.loads(data)
    if "id" not in att_data:
        return {"code": 400, "err": "Attendance not found"}

    if(len(att_data["id"]) > 20):
        enqueue("empg_erp.attendence.report.daily_attendance_report.daily_attendance_report.update_attendance", att_data = att_data)
        return {"code": 200, "success": "Attendance has been updated in the background"}
    else:
        response = update_attendance(att_data)
        return response


def update_attendance(att_data):
    response = []
    for att_id in att_data["id"]:

        try:
            attendance = frappe.get_doc("Attendance", att_id)
            if bool(attendance):

                if (checking_attandence_processed(attendance) == False):
                    return {"code": 400, "err": "You cannot update attendance after being processed"}

                parent_status = None
                if 'attendance_status' in att_data:
                    parent_status = frappe.db.get_value("Roster Status", {"name": att_data["attendance_status"]},
                                                        "parent_status", debug=True)


                new_doc = frappe.copy_doc(attendance)
                attendance.flags.ignore_permissions = True
                new_doc.flags.ignore_permissions = True

                attendance.cancel()

                if parent_status != None:
                    new_doc.status = parent_status
                if 'shift_start_time' in att_data:
                    new_doc.shift_start_time = att_data["shift_start_time"]
                if 'shift_end_time' in att_data:
                    new_doc.shift_end_time = att_data["shift_end_time"]
                if 'attendance_status' in att_data:
                    new_doc.attendance_status = att_data["attendance_status"]

                new_doc.amended_from = attendance.name
                new_doc.modified_by = frappe.session.user

                new_doc.save()
                new_doc.submit()

                response.append({"code": 200, "success": "sucess"})

            else:
                response.append({"code": 400, "err": "Attendance not found"})


        except Exception as err:
            response.append({"code": 500, "err": err})

    return response
