# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta
import json
from empg_erp.utils import get_limit_from_filters,\
	get_page_count, path_child, unlock_doc, get_time_diff, check_advance_privilege_by_name, get_config_by_name, \
	get_user_filters_by_role,get_auth_team_ids
from empg_erp.modules.mustang.shift import get_employee_shift
from empg_erp.constants.globals import PAGE_SIZE
from empg_erp.utils import get_start_end_date_of_last_week,get_formatted_hours
from frappe.utils import time_diff_in_hours

def get_list(filters, type = "query"):

	limit = str(PAGE_SIZE)
	start_day_date, end_day_date = get_start_end_date_of_last_week()

	try:
         employee_data = frappe.db.sql("""
           Select   empatt.name as name,
	          		empatt.company as company,
	          		IF(empatt.employee_name is null,'-',empatt.employee_name) employee_name,
	          		IF(le.leave_type IS NULL AND empatt.check_out IS NULL AND empatt.check_in IS NULL AND empatt.attendance_status = 'On', "Not Applied",
                    IF(COUNT(le.leave_type) > 1, "Multiple Leaves Applied", le.leave_type))as leave_type,
	          		le.status as leave_status,
	          		tabEmp.department as department,
	          		empatt.attendance_request as attendance_request,
	          		empatt.attendance_date as attendance_date,
	          		empatt.employee as employee,
	          		empatt.check_out as check_out,
	          		empatt.check_in as check_in,
	          		IF(empatt.late_arrival is null OR empatt.late_arrival < 0,'-',empatt.late_arrival) as late_arrival,
	          		IF(empatt.left_early is null OR empatt.left_early < 0,'-',empatt.left_early) as left_early,
	          		IF(empatt.working_hours is null,'-',empatt.working_hours) as working_hours,
	          		empatt.empghr_employee_attendance_pull_id as empghr_employee_attendance_pull_id,
	          		empatt.attendance_status as attendance_status,
	          		IF(empatt.shift_start_time is null,'-',empatt.shift_start_time) shift_start_time,
	          		IF(empatt.shift_end_time is null,'-',empatt.shift_end_time) shift_end_time,
	          		IF(ats.color is null,'#428b46',ats.color) as color,
	          		ats.name as status_name
          from `tabAttendance` As empatt
          INNER JOIN `tabEmployee` AS tabEmp ON empatt.employee = tabEmp.employee 
          LEFT JOIN `tabRoster Status` ats ON ats.name = empatt.attendance_status
          LEFT JOIN `tabLeave Application` le on empatt.employee = le.employee 
		  AND (empatt.attendance_date between le.from_date and le.to_date) AND le.docstatus < 2
          Where empatt.docstatus = 1
		  and empatt.attendance_date >= '{0}' and empatt.attendance_date <= '{1}'
		  and empatt.employee = '{2}'
		  GROUP BY empatt.employee, empatt.attendance_date
		  ORDER BY empatt.attendance_date DESC
          """.format(start_day_date, end_day_date, filters['userId']), as_dict=True)
         return employee_data

	except:
		return []

def execute(filters=None):
	columns, data = [], []

	limit = str(PAGE_SIZE)
	if "page" in filters:
		limit = filters["page"]

	if 'user' not in filters:
		userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
	else:
		userId = frappe.db.get_value("Employee", {"user_id": filters['user']}, "employee")
	
	filters['userId'] = userId
	att_list = get_list(filters)

	for att in att_list:

		_check_in = '-'
		_check_out = '-'

		if att.check_in :
			_check_in = datetime.strftime(att.check_in, "%H:%M:%S")

		if att.check_out :
			_check_out = datetime.strftime(att.check_out, "%H:%M:%S")

		_data = list()


		_data.append(att.attendance_date)
		_data.append(datetime.strftime(att.attendance_date, "%a"))

		if att.shift_start_time != '-':
			formatted_time = att.shift_start_time.split('.')
			att.shift_start_time = formatted_time[0]

		_data.append(att.shift_start_time)

		shift_working_hours = '-'
		if att.shift_start_time != '-' and att.shift_end_time != '-':
			if att.shift_start_time > att.shift_end_time:
				EndDate = att.attendance_date + timedelta(days=1)
				att.shift_end_time = "{} {}".format(EndDate, att.shift_end_time)

			else:
				att.shift_end_time = "{} {}".format(att.attendance_date, att.shift_end_time)

			att.shift_start_time = "{} {}".format(att.attendance_date, att.shift_start_time)

			shift_working_hours = int(time_diff_in_hours(att.shift_end_time,att.shift_start_time))

		_data.append(shift_working_hours)
		attendance_status = ''
		if(att.attendance_status is not None):
			attendance_status = """<div class='text-left'><span class='indicators-shift' style='background-color:{1}'></span>{0}</div>""".format(att.attendance_status,
																							att.color)
		_data.append(attendance_status)
		_data.append(_check_in)
		_data.append(_check_out)
		_data.append(att.late_arrival)
		left_early = ''
		if att.left_early is not None:
			left_early = str(att.left_early)
		_data.append(left_early)

		if att.working_hours != '-':
			att.working_hours = get_formatted_hours(att.working_hours)

		_data.append(att.working_hours)

		leave_type = '-'
		if att.leave_type is not None:
			if att.leave_type != 'Multiple Leaves Applied' and att.leave_status is not None:
				leave_type = "{0}-{1}".format(att.leave_status, att.leave_type)
			else:
				leave_type = att.leave_type

		_data.append(leave_type)

		data.append(_data)

	columns = [
		  _("Date")+ ":Date:100", _("Day")+ "::40",_("Shift Start")+ "::100",_("Shift Working Hours")+ "::100", _("Roster")+ "::70",
		_("Checkin-Time")+ "::10", _("Checkout-Time")+ "::10", _("Arrived Late By(mins)")+ "::10",
		 _("Left Early By(mins)")+ "::10",  _("Working Hours")+ "::40", _("Leave Applied")+ "::160"
	]
	
	return columns, data
