# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, date_diff, getdate, datetime, nowdate, get_datetime
from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange
from erpnext.hr.doctype.leave_application.leave_application import LeaveApplication, is_lwp
from erpnext.hr.doctype.leave_application.leave_application import get_leave_allocation_records, get_leaves_for_period, get_leave_approver,add_department_leaves, \
add_leaves, add_block_dates, add_holidays, get_leave_balance_on
from empg_erp.modules.mustang.shift import get_employee_shift, get_holiday_list_from_employee_shift
from empg_erp.utils import get_time_diff,get_config_by_name,str_to_date,check_advance_privilege_by_name, \
get_employee_code,get_auth_team_ids,get_user_role, get_employee_shift_timings
from empg_erp.constants.globals import CASUAL_LEAVE_TYPE,ROSTER_STATUS_OFF,HR_MANAGER,ADMINISTRATOR, \
LINE_MANAGER,EMPLOYEE,LEAVE_STATUS_APPROVED,ATTENDANCE_STATUS_ON_LEAVE,ATTENDANCE_STATUS_HALF_DAY_LEAVE, \
ATTENDANCE_STATUS_HOURLY_LEAVE, ATTENDANCE_STATUS_PRESENT, ATTENDANCE_STATUS_ABSENT, ROSTER_STATUS_ON, LEAVE_STATUS_REJECTED, LEAVE_STATUS_CANCELLED
import dateutil.relativedelta
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
from empg_erp.modules.common.error_handler import ErrorHandler

#TODO: Make separate file as constants for error messages
off_day_leave_err = "You cannot apply leave on Holiday/Off Day."

def validate_leave_overlap_override(doctype):
	if not doctype.name:
		# hack! if name is null, it could cause problems with !=
		doctype.name = "New Leave Application"

	for d in frappe.db.sql("""
		select
			name, leave_type, posting_date, from_date, to_date, total_leave_days, half_day_date, hourly_day_date
		from `tabLeave Application`
		where employee = %(employee)s and docstatus < 2 and status in ("Open", "Approved")
		and to_date >= %(from_date)s and from_date <= %(to_date)s
		and name != %(name)s""", {
			"employee": doctype.employee,
			"from_date": doctype.from_date,
			"to_date": doctype.to_date,
			"name": doctype.name
		}, as_dict = 1):

		if ((cint(doctype.half_day)==1 or cint(doctype.hourly)==1) and (
			getdate(doctype.half_day_date) == getdate(d.half_day_date) or getdate(doctype.hourly_day_date) == getdate(d.hourly_day_date))) and (
			getdate(doctype.from_date) == getdate(d.to_date)
			or getdate(doctype.to_date) == getdate(d.from_date)):

			total_leaves_on_half_day = get_total_leaves_on_a_day(doctype)

			if total_leaves_on_half_day > 1:
				doctype.throw_overlap_error(d)
		else:
			doctype.throw_overlap_error(d)

def validate_attendance_override(doctype):
	attendance = frappe.db.sql("""SELECT att.name 
		FROM 
			`tabAttendance` AS att
		INNER JOIN 
            `tabRoster Status` AS att_statuses
        ON
            att.attendance_status = att_statuses.name AND att_statuses.can_apply_leave = 0
		WHERE 
			att.employee = %s AND (att.attendance_date between %s AND %s) AND
		 	att.status = "Present" and att.docstatus = 1 """,(doctype.employee, doctype.from_date, doctype.to_date))
	
	total_leave_days = get_number_of_leave_days(doctype.employee, doctype.leave_type,doctype.from_date, doctype.to_date, doctype.half_day, doctype.half_day_date,doctype.hourly, doctype.hourly_day_date, doctype.hours)
	if attendance:
		if(total_leave_days == 0):
			frappe.throw(_(off_day_leave_err))

def validate_dates(doctype,event_name):
	''' validate cutoff dates '''

	try:
		date_obj = datetime.datetime.now()
		la_date = str_to_date(date_obj.strftime("%Y-%m-%d"), '%Y-%m-%d')
		processding_date = str_to_date(date_obj.strftime("%Y-%m-")+str(get_config_by_name('MONTH_PROCESSING_DATE','20')), '%Y-%m-%d')
		restrict_leave_date = str_to_date(date_obj.strftime("%Y-%m-")+str(get_config_by_name('RESTRICTED_LEAVES_DATE','22')), '%Y-%m-%d')
		from_date = str_to_date(doctype.from_date, '%Y-%m-%d')
		to_date = str_to_date(doctype.to_date, '%Y-%m-%d')
	except Exception as err:
		print(err)
		ErrorHandler.log_error(str(err))	
	
	''' if there is creation date then we consider creation date as leave application date la_date '''
	if hasattr(doctype, 'creation'):
		la_date = str_to_date(get_datetime(doctype.creation), '%Y-%m-%d')
	
	new_la = False
	if hasattr(doctype, '__islocal'):
		new_la = True

	''' Check advance privilege and validate dates of cutoff'''
	if(check_advance_privilege_by_name(get_config_by_name('ADVANCE_PRIV_APPLY_LEAVE_AFTER_CUTOFF_DATE')) == False  and new_la == True):
		if(la_date >= restrict_leave_date and (from_date <= processding_date or to_date <= processding_date )):
			frappe.throw(_("You cannot apply for a previous day leave after the cutoff date"))
		elif((from_date <= processding_date - dateutil.relativedelta.relativedelta(months=1) or to_date <= processding_date - dateutil.relativedelta.relativedelta(months=1))):
			frappe.throw(_("You cannot apply for a previous day leave after the cutoff date"))
	#TODO: Make validation configurable 
	''' Check advance privilege Validation for casual leave '''
	# if(CASUAL_LEAVE_TYPE == doctype.leave_type and check_advance_privilege_by_name(get_config_by_name('ADVANCE_PRIV_APPLY_CASUAL_LEAVE_FOR_PAST_DATES')) == False):
	# 	if((la_date > from_date or la_date > to_date) and new_la == True):
	# 		frappe.throw(_("Casual leave can only be applied for current/present or future date."))
    			

def validate_override(doctype,event_name):
	''' Function to override leaves validation for cutoff dattes and leave counts '''
	from empg_erp.modules.common.leave_application import validate_leave_approver
	validate_dates(doctype,event_name)
	validate_leave_approver(doctype)
	validate_leave_approver_comments(doctype)
	validate_halfday_hourly_checks(doctype)

def update_attendance_override(self):
    ''' Function to overide Roster Statuses on applying leaves'''
    if self.status == LEAVE_STATUS_APPROVED:
		attendance = frappe.db.sql("""select name from `tabAttendance` where employee = %s\
			and (attendance_date between %s and %s) and docstatus < 2""",(self.employee, self.from_date, self.to_date), as_dict=1)
		if attendance:
			for d in attendance:
				doc = frappe.get_doc("Attendance", d.name)
				status = ATTENDANCE_STATUS_ON_LEAVE
				if (self.half_day and getdate(self.half_day_date) == doc.attendance_date):
					status = ATTENDANCE_STATUS_HALF_DAY_LEAVE
				if (self.hourly and getdate(self.hourly_day_date) == doc.attendance_date):
					status = ATTENDANCE_STATUS_HOURLY_LEAVE
				frappe.db.sql("""update `tabAttendance` set status = %s, leave_type = %s\
					where name = %s""",(status, self.leave_type, d.name))

		else:
			for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
				date = dt.strftime("%Y-%m-%d")
				if get_holidays(self.employee, date, date) == 0:
					doc = frappe.new_doc("Attendance")
					doc.employee = self.employee
					doc.employee_name = self.employee_name
					doc.attendance_date = date
					doc.company = self.company
					shift_detail = get_employee_shift_timings(self.employee)
					if shift_detail:
						doc.shift_start_time = shift_detail.start_time
						doc.shift_end_time = shift_detail.end_time
					doc.leave_type = self.leave_type
					doc.attendance_status = ROSTER_STATUS_ON
					doc.status = ATTENDANCE_STATUS_ON_LEAVE
					if (self.half_day and date == self.half_day_date):
						doc.status = ATTENDANCE_STATUS_HALF_DAY_LEAVE
					elif (self.hourly and date == self.hourly_day_date):
						doc.status = ATTENDANCE_STATUS_HOURLY_LEAVE    				
					doc.flags.ignore_validate = True
					doc.insert(ignore_permissions=True)
					doc.submit()

def cancel_attendance_override(self):
	if self.docstatus == 2:
		attendance = frappe.db.get_all('Attendance',
			filters={
				'employee': self.employee,
				'attendance_date':['between',(self.from_date, self.to_date)],
				'docstatus':['<',2],
				'status': ['in', (ATTENDANCE_STATUS_ON_LEAVE, ATTENDANCE_STATUS_HALF_DAY_LEAVE, ATTENDANCE_STATUS_HOURLY_LEAVE)]
			},
			fields=['name','attendance_date']
		)

		for obj in attendance:
			if(datetime.date.today() < obj.attendance_date):
				frappe.db.set_value("Attendance", obj.name, "docstatus", 2)

def get_total_leaves_on_a_day(doctype):
	''' Function to sum number of leave hours on a date'''
	applied_leaves_on_date = frappe.db.sql("""select SUM(total_leave_days) from `tabLeave Application`
	where employee = %(employee)s
	and docstatus < 2
	and status in ("Open", "Approved")
	and ((half_day = 1 and half_day_date = %(half_day_date)s) OR (hourly = 1 and hourly_day_date = %(half_day_date)s) OR (%(from_date)s BETWEEN from_date AND to_date) OR (%(to_date)s BETWEEN from_date AND to_date) )
	and name != %(name)s
	""", {
		"employee": doctype.employee,
		"half_day_date": doctype.half_day_date,
		"from_date": doctype.from_date,
		"to_date": doctype.to_date,
		"name": doctype.name
	})[0][0]

	return flt(applied_leaves_on_date) + flt(get_number_of_leave_days(doctype.employee, doctype.leave_type,doctype.from_date, doctype.to_date, doctype.half_day, doctype.half_day_date,doctype.hourly, doctype.hourly_day_date, doctype.hours))


def before_save_override(doctype,event_name):
	'''Override Function to total_leave_days to total_leave_days_override for
	leaves ( Because we add hourly leave functionality)'''
	doctype.total_leave_days = get_number_of_leave_days(doctype.employee, doctype.leave_type,doctype.from_date, doctype.to_date, doctype.half_day, doctype.half_day_date,doctype.hourly, doctype.hourly_day_date, doctype.hours)
	if (doctype.total_leave_days <= 0):
		frappe.throw(_("You cannot apply leave on Off Day"))

	''' Add restriction on update leave application only status and comments are updating'''
	if event_name == 'before_save':
		if not hasattr(doctype, '__islocal'):
			doc = frappe.get_doc("Leave Application", doctype.name)
			_status = doctype.status
			_comment = doctype.leave_approver_comments
			doctype.__dict__.update(doc.__dict__)
			doctype.status = _status
			doctype.leave_approver_comments = _comment

def validate_balance_leaves(self):
	if self.from_date and self.to_date:
		"""
		overriding starts
		"""
		self.total_leave_days = get_number_of_leave_days(self.employee, self.leave_type,
		self.from_date, self.to_date, self.half_day, self.half_day_date, self.hourly, 
		self.hourly_day_date, self.hours)
		"""
		overriding ends
		"""

	if self.total_leave_days <= 0:
		frappe.throw(_("The day(s) on which you are applying for leave are holidays"))

	if not is_lwp(self.leave_type):
		self.leave_balance = get_leave_balance_on(self.employee, self.leave_type, self.from_date, docname=self.name,
			consider_all_leaves_in_the_allocation_period=True)
		
		if self.status != "Rejected" and self.leave_balance < self.total_leave_days:
			if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
				frappe.msgprint(_("Note: There is not enough leave balance for Leave Type {0}")
					.format(self.leave_type))
			else:
				frappe.throw(_("There is not enough leave balance for Leave Type {0}")
					.format(self.leave_type))


@frappe.whitelist()
def get_number_of_leave_days(employee = None, leave_type = None, from_date = None, to_date = None, half_day = None, half_day_date = None,hourly = None, hourly_day_date = None, hours= None):
	'''Override white listed function get_number_of_leave_days for calculate 
	leave days ( Because we calcuate leaves according to hourly functionality)'''
	number_of_days = 0
	h_h_date = None
	if cint(half_day) == 1:
		h_h_date = half_day_date
		if from_date == to_date:
			number_of_days = 0.5
		else:
			number_of_days = date_diff(to_date, from_date) + .5
	elif cint(hourly) == 1:
		shift_date = h_h_date = to_date
		if(hourly_day_date):
			shift_date = h_h_date = hourly_day_date
		shift = get_employee_shift(employee,shift_date)
		today_shift_start = "{0} {1}".format(shift_date, shift.start_time)
		today_shift_end = "{0} {1}".format(shift_date, shift.end_time)
		working_hours  = get_time_diff(today_shift_end,today_shift_start,'hours')

		if(working_hours <= 0):
			frappe.throw("Invalid shift start and end time")
		if from_date == to_date:
			number_of_days = round((float(1.00/working_hours)*float(hours)),2)
		else:
			number_of_days = date_diff(to_date, from_date) + round((float(1.00/working_hours)*float(hours)),2)
	else:
		number_of_days = date_diff(to_date, from_date) + 1		
	
	if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		holidays, holiday_dates = get_holidays(employee, from_date, to_date, True)
		if h_h_date is not None and h_h_date:
			h_h_date = str_to_date(h_h_date, '%Y-%m-%d')
			for holiday_date in holiday_dates:
				if h_h_date == str_to_date(holiday_date, '%Y-%m-%d'):
					number_of_days = int(number_of_days)
					holidays = holidays-1

		number_of_days = flt(number_of_days) - flt(holidays)
	if(number_of_days < 0):
		return 0
	return number_of_days

@frappe.whitelist()
def get_leave_details(employee, date):
	'''Override white listed function get_leave_details for calculate leaves details
	Because after adding hourly leave funcionality leave balanace, leave used and pending leaves qouta calculted in decimals and 
	this add almost 10+ digits after decimal'''
	allocation_records = get_leave_allocation_records(date, employee).get(employee, frappe._dict())
	leave_allocation = {}
	for d in allocation_records:
		allocation = allocation_records.get(d, frappe._dict())
		date = allocation.to_date
		leaves_taken = round(get_leaves_for_period(employee, d, allocation.from_date, date, status="Approved"),2)
		leaves_pending = round(get_leaves_for_period(employee, d, allocation.from_date, date, status="Open"),2)
		remaining_leaves = round(allocation.total_leaves_allocated - leaves_taken - leaves_pending,2)
		leave_allocation[d] = {
			"total_leaves": allocation.total_leaves_allocated,
			"leaves_taken": leaves_taken,
			"pending_leaves": leaves_pending,
			"remaining_leaves": remaining_leaves}

	ret = {
		'leave_allocation': leave_allocation,
		'leave_approver': get_leave_approver(employee)
	}

	return ret

def get_leave_allocation_detail(employee, leave_type, from_date, to_date):

	leave_allocations = frappe.db.sql("""
		select name, employee, leave_type, from_date, to_date, total_leaves_allocated
		from `tabLeave Allocation`
		where employee=%(employee)s and leave_type=%(leave_type)s
			and docstatus=1
			and (from_date between %(from_date)s and %(to_date)s
				or to_date between %(from_date)s and %(to_date)s
				or (from_date < %(from_date)s and to_date > %(to_date)s))
	""", {
		"from_date": from_date,
		"to_date": to_date,
		"employee": employee,
		"leave_type": leave_type
	}, as_dict=1)

	return leave_allocations

@frappe.whitelist()
def get_leave_approver(employee, department=None):
	leave_approver = ""
	employee_detail = frappe.db.get_value('Employee', employee, ['department','reports_to','user_id'])
	
	if employee_detail and employee_detail[1]:
		leave_approver = frappe.db.get_value('Employee', employee_detail[1], 'user_id')
    	
	if not leave_approver and employee_detail and employee_detail[0]:
		leave_approver = frappe.db.get_value('Department Approver', {'parent': employee_detail[0],
		'parentfield': 'leave_approvers', 'idx': 1}, 'approver')

	if leave_approver is None and check_advance_privilege_by_name(get_config_by_name('ADVANCE_PRIV_AUTO_APPROVE_LEAVE')):
		if employee_detail and employee_detail[2] and frappe.session.user != ADMINISTRATOR:
			leave_approver =  employee_detail[2]
	return leave_approver

@frappe.whitelist()
def get_holidays(employee, from_date, to_date, dates=False):
	''' get attendance with status '''

	from empg_erp.modules.mustang.attendance.employee_attendance import get_employee_attendance

	employee_attendance = get_employee_attendance(employee, from_date, to_date)
	_attendance_dates = []
	_off_day_dates = []
	_off_days = 0
	if(employee_attendance):
		for attendance in employee_attendance:
			if(attendance.can_apply_leave == 0):
				_off_days = _off_days+1
				_off_day_dates.append(attendance.attendance_date)
			_attendance_dates.append(attendance.attendance_date)	

	_excclude_condition = _in_holiday_condition = ''
	if(_attendance_dates):
		_excclude_condition = " AND h1.holiday_date NOT IN ({0})".format(','.join('\'{0}\''.format(date.strftime("%Y-%m-%d")) for date in _attendance_dates))

	'''get holidays between two dates for the given employee'''
	all_holiday_list = []
	'''get holiday list from employee shift'''
	holiday_list_from_employee =  get_holiday_list_from_employee_shift(employee)
	if(holiday_list_from_employee and holiday_list_from_employee not in all_holiday_list):
		all_holiday_list.append(holiday_list_from_employee)
	'''get holiday list for employee by company or by employee'''
	holiday_list = get_holiday_list_for_employee(employee)
	if holiday_list not in all_holiday_list:
		all_holiday_list.append(holiday_list)
	'''get distinct holiday dates'''
	
	if(all_holiday_list):
		_in_holiday_condition = " AND h2.name IN ({0})".format(','.join('\'{0}\''.format(list) for list in all_holiday_list))
	
	holidays = frappe.db.sql("""select distinct holiday_date from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %(from_date)s AND %(to_date)s 
		{0} {1}""".format(_in_holiday_condition, _excclude_condition),({"from_date":from_date, "to_date":to_date}))
	if(len(holidays)>0):
		for holiday_date in holidays:
			if holiday_date[0] not in _off_day_dates:
				_off_day_dates.append(holiday_date[0])
	if dates == False:
		return len(holidays)+_off_days
	return len(holidays)+_off_days,_off_day_dates


def validate_leave_approver_comments(doctype):
	if(doctype.status in [LEAVE_STATUS_REJECTED, LEAVE_STATUS_CANCELLED] and not doctype.leave_approver_comments):
		frappe.throw(_("Comments are required to reject/cancel leave."))

def update_leave_approver(employee,leave_approver):
	employee_detail = frappe.db.get_value('Employee', leave_approver, ['user_id','employee_name'])
	if(employee_detail):
		if employee_detail[0] is not None:
			try:
				frappe.db.sql(""" UPDATE `tabLeave Application` la
				SET
					la.leave_approver = %(user_id)s , la.leave_approver_name = %(employee_name)s
				WHERE
					la.employee = %(employee)s AND la.docstatus = 0
				""",({"user_id":employee_detail[0], "employee_name":employee_detail[1], "employee":employee}))
			except Exception as err:
				ErrorHandler.log_error(str(err))
				frappe.throw(_("Unable to update leave approver"))
		else:
			frappe.throw(_("No user id linked with employee {0}".format(leave_approver)))

def update_leave_days(dates=[],update=False):
	#  get_number_of_leave_days(doctype.employee, doctype.leave_type,doctype.from_date, doctype.to_date, doctype.half_day, doctype.half_day_date,doctype.hourly, doctype.hourly_day_date, doctype.hours)
	for date in dates:
		try:
			leave_applications = frappe.db.get_all('Leave Application',
				filters={
					'to_date':['>=',date],
					'from_date': ['<=',date]
				},
				fields=['name']
			)
			for la in leave_applications:
				doc  = frappe.get_doc("Leave Application", la.name)
				frappe.db.set_value("Leave Application", la.name, "total_leave_days", get_number_of_leave_days(doc.employee, doc.leave_type,doc.from_date, doc.to_date, doc.half_day, doc.half_day_date,doc.hourly, doc.hourly_day_date, doc.hours))
		except Exception as err:
			frappe.throw(_("Unable to update Leave Application"))

def validate_halfday_hourly_checks(doctype):
	hh_date = None

	if doctype.half_day:
		hh_date = str_to_date(doctype.half_day_date)
	if doctype.hourly:
		hh_date = str_to_date(doctype.hourly_day_date)

	date_obj = datetime.datetime.now()
	current_date = str_to_date(date_obj.strftime("%Y-%m-%d"), '%Y-%m-%d')

	if hh_date and  hh_date < current_date:
		if frappe.db.exists("Attendance",{"employee": doctype.employee, "attendance_date":hh_date, "status":ATTENDANCE_STATUS_ABSENT,"docstatus":1}):
			frappe.throw(_("You cannot apply half day or hourly leave because you were absent."))