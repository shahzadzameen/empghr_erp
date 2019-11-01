from datetime import datetime, timedelta
import frappe
from frappe import _
import calendar
from frappe.utils import getdate, nowdate
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.utils import get_config_by_name, get_monthly_diff_dates, get_time_diff, get_timestamp,get_employee_code,check_advance_privilege_by_name,copy_fields,unlock_doc,get_previous_version
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE,LEAVE_STATUS_APPROVED,ATTENDANCE_MANAGER,LINE_MANAGER,ADMINISTRATOR,ROSTER_STATUS_HOLIDAY
from erpnext.hr.doctype.attendance.attendance import Attendance
from empg_erp.modules.mustang.employee_penalty.attendance_penalty import AttendancePenalty
from empg_erp.empg_erp.doctype.attendance_penalties_processed.attendance_penalties_processed import check_processed
from frappe.utils.background_jobs import enqueue
from erpnext.hr.utils import divide_chunks


class EmployeeAttendance():

    def __init__(self):

        self.employee = None
        # self.shift = None
        self.grace_mins = None
        self.attendance_date = None
        self.check_in = None
        self.late_arrival  = None
        self.check_out = None
        self.left_early = None
        self.working_hours = None
        self.status = "Present"
        self.docstatus = 1
        self.shift_start_time = None
        self.shift_end_time = None
        self.set_by_cron = 1
        self.calculate_penalties = 1

    @property
    def check_in(self):
        return self.check_in

    @check_in.setter
    def check_in(self, check_in):
        if(isinstance(check_in, str) or isinstance(check_in, unicode)):
            self.check_in = check_in
        else:
            self.check_in = datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S")

    @property
    def check_out(self):
        return self.check_out

    @check_out.setter
    def check_out(self, check_out):
        if(isinstance(check_out, str) or isinstance(check_out, unicode)):
            self.check_out = check_in
        else:
            self.check_out = datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S")

def on_submit(doc, event):

    if((("set_by_cron" not in doc.__dict__) or ("calculate_penalties" in doc.__dict__)) and checking_attandence_processed(doc)):

        _today = datetime.strptime(str(doc.attendance_date), "%Y-%m-%d")
        _month = _today.month
        _day = _today.day

        if _day > MONTHLY_ATTENDANCE_DATE:
            _month = int(_month) + 1

        date_start, date_end = get_monthly_diff_dates(day=MONTHLY_ATTENDANCE_DATE, month=_month)
        penalty = AttendancePenalty(date_start, date_end)
        penalty.calculate_employee_penalties(doc.employee)

# def on_cancel(doc, event):

#     if(checking_attandence_processed(doc) == False):
#         frappe.throw(_("You cannot cancel attendance after being processed"))
#     # Restrict self cancel for Attendance
#     if doc.employee is not None:
#         if doc.employee == get_employee_code():
#             frappe.throw(_("You cannot cancel your attendance"))
    

def before_save_attendance(doc, event):

    if doc.attendance_status == ROSTER_STATUS_HOLIDAY and doc.flags.ignore_permissions == False:
        frappe.throw(_("You cannot manually update roster status to holiday"))

    calculate_late_arrivals(doc)

    doc.shift_start_time = doc.shift_start_time if doc.shift_start_time != None else get_config_by_name("default_shift_start_time", "09:00:00")
    doc.shift_end_time = doc.shift_end_time if doc.shift_end_time != None else get_config_by_name("default_shift_end_time", "18:00:00")

    user_id = frappe.session.user
    auth_role = frappe.get_roles(user_id)


    emp_attendance = []
    if doc.amended_from is not None:
        emp_attendance = frappe.db.get_value("Attendance", {"name": doc.amended_from}, "*")

    if ADMINISTRATOR != user_id:
        # if(emp_attendance):
        #     emp_attendance.attendance_date = emp_attendance.attendance_date.strftime('%Y-%m-%d')
        #     # Only employee with advanced privilege can update privious date attendance for roster
        #     today_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
        #     if emp_attendance.attendance_date < today_date and check_advance_privilege_by_name(get_config_by_name('CAN_UPDATE_PREVIOUS_DAY_ROSTER')) == False:
        #         frappe.throw(_("You cannot update previous date roster"))

        # Validate not to update attendance except AttendanceManager
        if ATTENDANCE_MANAGER not in auth_role and doc.flags.ignore_permissions == False:
            if emp_attendance:

            # validate for attendance_date
                if doc.attendance_date is not None:
                    if str(doc.attendance_date) != str(emp_attendance.attendance_date):
                        frappe.throw(_("You cannot update attendance date"))
            # validate for check_in
                if doc.check_in is not None:
                    if str(doc.check_in) != str(emp_attendance.check_in):
                        frappe.throw(_("You cannot update attendance check in time"))

            # validate for check_out
                if doc.check_out is not None:
                    if str(doc.check_out) != str(emp_attendance.check_out):
                        frappe.throw(_("You cannot update attendance check out time"))
            # validate for employee_id
                if doc.employee is not None:
                    if doc.employee != emp_attendance.employee:
                        frappe.throw(_("You cannot update employee code"))


        # Restrict self update for Attendance
        if doc.employee is not None:
            if doc.employee == get_employee_code():
                frappe.throw(_("You cannot update your attendance"))


def before_submit_attendance(doc, event):

    if("set_by_cron" not in doc.__dict__):
        create_attendance_log(doc, event)

def create_attendance_log(doc,event):
    try:
            _at_log = frappe.get_doc({"doctype": "Attendance Log"})
            attendance_data = frappe.get_doc("Attendance", doc.name)

            filelds_to_copy = ["employee", "employee_name", "status", "leave_type", "attendance_date", "company", "department",
                 "attendance_request",
                 "attendance_status", "shift_start_time", "shift_end_time", "check_in", "check_out",
                 "late_arrival", "left_early", "working_hours", "empghr_employee_attendance_pull_id",
                 "empghr_employee_line_manager_pull_id"]

            copy_fields(
                    _at_log, attendance_data,filelds_to_copy
                )

            _at_log.attendance_name = doc.name
            _at_log.insert()

    except Exception as err:
        ErrorHandler.log_error(str(err))
        frappe.throw(err)


def checking_attandence_processed(doctype):
	'''Checking Attendance Processed or Not'''

	attendance_date = datetime.strptime(str(doctype.attendance_date), "%Y-%m-%d")
	attendance_month = attendance_date.month
	attendance_year = attendance_date.year

	return not check_processed(doctype.employee, attendance_month, attendance_year, doctype.attendance_date)

# after save - calculating late arivals etc
def calculate_late_arrivals(doctype):

    attendance_date = datetime.strptime(str(doctype.attendance_date), "%Y-%m-%d")
    attendance_month = attendance_date.month
    attendance_year = attendance_date.year

    if check_processed(doctype.employee, attendance_month, attendance_year, doctype.attendance_date) == True:
        frappe.throw(_("Attendance Cannot be updated after bieng processed"))
    	
	# Calculate Late Arrivals, Working hours, Left Early
    
    if(doctype.shift_start_time and doctype.shift_end_time):
        try:
            if(doctype.check_in and doctype.check_out):
                doctype.working_hours = get_time_diff(doctype.check_out, doctype.check_in, "hours")
            
            attendance_date = attendance_date.strftime("%Y-%m-%d")
            shift_start = "{} {}".format(attendance_date, doctype.shift_start_time)
            shift_end = "{} {}".format(attendance_date, doctype.shift_end_time)

            if get_timestamp(shift_end) < get_timestamp(shift_start):
                _shift_start = datetime.strptime(shift_end, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
                shift_end = datetime.strftime(_shift_start, "%Y-%m-%d %H:%M:%S")
           
            if(doctype.check_in):
                doctype.late_arrival = get_time_diff(doctype.check_in, shift_start,"mins")
            
            if(doctype.check_out):
                doctype.left_early = get_time_diff(shift_end, doctype.check_out, "mins")
            else:
                doctype.left_early = 0
                    
        except Exception as err:
            print(err)


def before_save_holiday_list(doc,event):

    list1 = doc.holidays

    _list1 = []

    for holiday in list1:
        _list1.append(holiday.name)

    if frappe.db.exists("Holiday List",doc.name):
        _holiday_list = frappe.get_doc("Holiday List", doc.name)
        list2 = _holiday_list.holidays

        _list2 = []
        _list2_dic = dict()
        for holiday in list2:
            _list2.append(holiday.name)
            _list2_dic[holiday.name] = holiday.holiday_date


        # get difference between both lists
        holdays_to_revert = list(set(_list1).symmetric_difference(set(_list2)))

        #get tintersection form privious list
        _holidays_to_revert = list(set(_list2).intersection(holdays_to_revert))

        _list_holiday_dates = []

        for holiday in _holidays_to_revert:
            if holiday in _list2_dic:
                _list_holiday_dates.append(_list2_dic[holiday])
        
        employee_list = frappe.db.sql("""
        SELECT e.name FROM `tabHoliday List` hl
        LEFT JOIN `tabCompany` comp on comp.default_holiday_list = hl.name
        LEFT JOIN `tabEmployee` e on e.company = comp.name
        WHERE hl.to_date >= DATE(now()) AND hl.name = "{0}" AND e.status != "Left"
        """.format(doc.name), as_dict=True)

        _max_iterations = 10000
        _iteration = 0
        _chunk = divide_chunks(employee_list, 20)
        while True or _iteration <= _max_iterations:
            try:
                queue_data = next(_chunk)
                enqueue("empg_erp.modules.mustang.attendance.employee_attendance.revert_holiday_status_on_removed_holidays", doc=doc,_list_holiday_dates=_list_holiday_dates,employee_list=queue_data)
                _iteration += 1
            except StopIteration:
                break

def revert_holiday_status_on_removed_holidays(doc,_list_holiday_dates,employee_list):

    if employee_list and len(_list_holiday_dates) > 0:

        _list = ','.join(('\'' + str(x) + '\'') for x in _list_holiday_dates)
        emp_Ids = ','.join(('\'' + str(x["name"]) + '\'') for x in employee_list)

        try:
            if _list != '':
                att_data = frappe.db.sql("""
                                   Select * from `tabAttendance`
                                   WHERE attendance_date IN ({0}) AND employee IN ({1}) AND docstatus = 1
                                   """.format(_list, emp_Ids), as_dict=True)

                for _att in att_data:

                    attendance = frappe.get_doc("Attendance", _att['name'])
                    if bool(attendance):
                        # saving version of document to track changes

                        # saving previous version
                        attendance_status = frappe.db.get_value("Attendance Log", {"attendance_name": attendance.name}, "attendance_status")
                        if (attendance_status):
                            unlock_doc("Attendance", _att['name'])
                            attendance._doc_before_save = attendance
                            attendance.attendance_status = attendance_status
                            parent_status = frappe.db.get_value("Roster Status", {"name" : attendance_status}, "parent_status")
                            if parent_status:
                                attendance.status = parent_status
                            attendance.docstatus = 1
                            attendance.save_version()
                            attendance.save()
        except Exception as err:
            frappe.throw(_("Unable to revert roster status"))
    if len(_list_holiday_dates)>0:
        from empg_erp.modules.mustang.leave_application.leave_application import update_leave_days
        update_leave_days(_list_holiday_dates)

def update_holiday_status(holiday_name, employee=[]):
    emp_list_name = []
    if len(employee) > 0 and 'name' not in employee[0]:
        for emp_name in employee:
            emp_dict = {
                "name": emp_name,
            }
            emp_list_name.append(emp_dict)

        employee = emp_list_name
    if holiday_name:
            _today = datetime.today()
            _current_month = _today.strftime("%m")
            _current_year = _today.strftime("%Y")

            today_date = _today.strftime("%Y-%m-%d")
            end_date = _today.strftime("%Y-12-31")

            holiday_list = frappe.db.sql("""
                SELECT holiday_date FROM `tabHoliday`
                WHERE parent = %(holiday_name)s AND holiday_date >= %(today_date)s AND holiday_date <= %(end_date)s
            """, {
                "holiday_name" : holiday_name,
                "today_date": today_date,
                "end_date" : end_date
            }, as_dict=True)

            _list = ''
            emp_Ids = ''

            if holiday_list and len(employee) > 0:
                _list = ','.join(('\'' + str(x["holiday_date"]) + '\'') for x in holiday_list)
                emp_Ids = ','.join(('\'' + str(x["name"]) + '\'') for x in employee)
                try:
                    if _list != '':
                        att_data = frappe.db.sql("""
                            Select * from `tabAttendance`
                            WHERE attendance_date IN ({0}) AND employee IN ({1}) AND docstatus = 1
                            """.format(_list, emp_Ids), as_dict=True)

                    for _att in att_data:

                        attendance = frappe.get_doc("Attendance", _att['name'])
                        if bool(attendance):

                         if (checking_attandence_processed(attendance) == True and (attendance.check_in is None or attendance.check_in == '' )and attendance.attendance_status != ROSTER_STATUS_HOLIDAY):
                            unlock_doc("Attendance", _att['name'])
                            # saving version of document to track changes
                            attendance._doc_before_save = attendance
                            # saving previous version
                            attendance.attendance_status = ROSTER_STATUS_HOLIDAY
                            parent_status = frappe.db.get_value("Roster Status", {"name" : ROSTER_STATUS_HOLIDAY}, "parent_status")
                            if parent_status:
                                attendance.status = parent_status
                            attendance.docstatus = 1
                            attendance.save_version()

                            attendance.save()

                except Exception as err:
                        frappe.throw(_("Unable to update attendance with roster status holiday"))
            if len(holiday_list)>0:
                from empg_erp.modules.mustang.leave_application.leave_application import update_leave_days
                _list = []
                for holiday in holiday_list:
                    _list.append(holiday.holiday_date)
                update_leave_days(_list)

def update_holiday_employee(doc, event):
    employee_list = frappe.db.sql("""
    SELECT e.name FROM `tabHoliday List` hl
    LEFT JOIN `tabCompany` comp on comp.default_holiday_list = hl.name
    LEFT JOIN `tabEmployee` e on e.company = comp.name
    WHERE hl.to_date >= DATE(now()) AND hl.name = "{0}" AND e.status != "Left"
    """.format(doc.name), as_dict=True)
    _max_iterations = 10000
    _iteration = 0
    _chunk = divide_chunks(employee_list, 20)
    while True or _iteration <= _max_iterations:
        try:
            queue_data = next(_chunk)
            enqueue("empg_erp.modules.mustang.attendance.employee_attendance.update_holiday_status", holiday_name= doc.name, employee = queue_data)
            _iteration += 1
        except StopIteration:
            break


def validate_attendance(self): 
    pass
    # date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

    # if date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
    #     frappe.throw(_("Attendance date can not be less than employee's joining date"))

def check_leave_record_override(self):
    leave_record = frappe.db.sql("""select leave_type, half_day,half_day_date, hourly, hourly_day_date from `tabLeave Application`
    where employee = %s and %s between from_date and to_date and status = %s
    and docstatus = 1""", (self.employee, self.attendance_date,LEAVE_STATUS_APPROVED), as_dict=True)
    if leave_record and self.docstatus == 1:
        for d in leave_record:
            if d.half_day  and d.half_day_date == getdate(self.attendance_date):
                self.status = 'Half Day'
                frappe.msgprint(_("Employee {0} on Half day on {1}").format(self.employee, self.attendance_date))
            elif d.hourly  and d.hourly_day_date == getdate(self.attendance_date):
                self.status = 'Hourly'
                frappe.msgprint(_("Employee {0} on Hourly Leave on {1}").format(self.employee, self.attendance_date))
            else:
                self.status = 'On Leave'
                self.leave_type = d.leave_type
                frappe.msgprint(_("Employee {0} is on Leave on {1}").format(self.employee, self.attendance_date))

    if self.status == "On Leave" and not leave_record:
        frappe.throw(_("No leave record found for employee {0} for {1}").format(self.employee, self.attendance_date))

def get_employee_attendance(employee,from_date,to_date):
    return frappe.db.sql("""SELECT att.attendance_date,rs.can_apply_leave,att.status 
        FROM 
            `tabAttendance` AS att
        LEFT JOIN 
            `tabRoster Status` AS rs
        ON
            att.attendance_status = rs.name
		WHERE 
            att.employee = %(employee)s AND attendance_date between %(from_date)s AND %(to_date)s 
            AND att.docstatus = 1
        """,({"employee":employee,"from_date":from_date, "to_date":to_date}), as_dict= 1)

def validate_override(self):
    from erpnext.controllers.status_updater import validate_status
    validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day","Hourly"])
    self.validate_attendance_date()
    self.validate_duplicate_record()
    self.check_leave_record()