# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt



from __future__ import unicode_literals
from empg_erp.constants.globals import PAGE_SIZE,LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR,EMPLOYEE
from empg_erp.utils import get_user_role,get_auth_team_ids,get_user_filters_by_role,get_start_end_date_of_last_week
import xml
import json
import frappe
import math
from frappe import _


def execute(filters=None):
	if not filters: filters = {}

	if 'user' not in filters:
		userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
	else:
		userId = frappe.db.get_value("Employee", {"user_id": filters['user']}, "employee")

	filters['userId'] = userId
	advances_list = get_conditions(filters)
	_roster_employee = []

	employee_data = getLateAttendenceEmployees(advances_list,userId)
	for emp in employee_data:
		row = []

		row.append(str(emp.employeeID))
		row.append(str(emp.EmployeeName))
		row.append(str(emp.Department))
		row.append(int(emp.LateArrivalInstance))
		row.append((int(emp.TotalLateArrivalMinutes)))

		_roster_employee.append(row)



	columns = [("Code") + "::140", ("Employee") + "::170",("Department") + "::150", ("Late Arrival Instances") + "::180", ("Late Arrival Total(mins)") + "::180"]
	return columns, _roster_employee


def get_conditions(filters):
	conditions = ""

	if filters.get("userId"):
		conditions += " AND tabEmp.reports_to = " + '\'' + filters.get("userId") + '\''

	return conditions


def remove_tags(text):
	return ''.join(xml.etree.ElementTree.fromstring(text).itertext())




def getLateAttendenceEmployees(advances_list ="",userId = None):

	start_date,end_date = get_start_end_date_of_last_week()

	if start_date and end_date:
		advances_list += " AND empatt.attendance_date between '{0}' AND '{1}' ".format(start_date, end_date)

	advances_list += " group by tabEmp.employee"
	employee_data = []
	if userId is not None:
		employee_data = frappe.db.sql("""
		SELECT 
			tabEmp2.employee_name As action_asset_name,
			tabEmp2.user_id As action_asset_email,
			empatt.employee AS employeeID,
			tabEmp.employee_name AS EmployeeName,
			tabEmp2.employee_name As ReportingManager,
			tabEmp.company AS Company,
			tabEmp.department AS Department,
			count(empatt.late_arrival) as LateArrivalInstance,
			sum(empatt.late_arrival) as TotalLateArrivalMinutes 
		FROM
		`tabAttendance` empatt
			LEFT JOIN 
		`tabRoster Status` eas ON eas.name = empatt.attendance_status
			LEFT JOIN
		`tabEmployee` AS tabEmp ON empatt.employee = tabEmp.employee
			 LEFT JOIN
		`tabEmployee` AS tabEmp2 ON tabEmp.reports_to = tabEmp2.employee
			WHERE empatt.late_arrival > 0
			AND eas.consider_penalty = 1
			AND empatt.docstatus = 1
			  """+ advances_list, as_dict=True
									  )


	return employee_data


