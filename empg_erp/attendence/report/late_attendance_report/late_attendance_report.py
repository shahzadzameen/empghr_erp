# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from empg_erp.constants.globals import PAGE_SIZE,LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR,EMPLOYEE
from empg_erp.utils import get_user_role,get_auth_team_ids,get_user_filters_by_role
import xml
import json
import frappe
import math
from frappe import _


def execute(filters=None):
	if not filters: filters = {}


	advances_list = get_conditions(filters)
	_roster_employee = []
	columns = []

	Limit = ""
	if filters.get("page"):
		concat = str(filters.get("page")).split('_')
		limit = str(concat[0])
	else:
		limit = str(PAGE_SIZE)
	Limit = " LIMIT " + limit

	limit = str(filters.get("page"))
	if limit == 'None':
		limit = str(PAGE_SIZE)

	AuthRole = getAuthRole()
	employee_data,dataLength = getLateAttendenceEmployees(advances_list,AuthRole,Limit)
	for emp in employee_data:
		row = []
		row.append(str(emp.employeeID))
		row.append(str(emp.EmployeeName))
		row.append(str(emp.ReportingManager))
		row.append(str(emp.Department))
		row.append(str(emp.sub_department))

		LateArrivalInstance = int(emp.LateArrivalInstance)
		row.append(late_arrival_pop(LateArrivalInstance, emp.employeeID))

		TotalLateArrivalMinutes = (int(emp.TotalLateArrivalMinutes))
		row.append(late_arrival_pop(TotalLateArrivalMinutes, emp.employeeID))

		_roster_employee.append(row)



	columns = [("Code<input type='hidden' value='"+limit+"' id='page' />") + "::140", ("Employee") + "::170", ("Reporting Manager") + "::170", ("Department") + "::120",
			   ("Sub Department") + "::150", ("Late Arrival Instances") + "::180", ("Late Arrival Total(mins)") + "::180"]
	return columns, _roster_employee


def get_conditions(filters):
	conditions = ""
	# if user filter has not assigned on page load and its not 'Administrator' then assign 'Me' by default
	if filters.get("user") is None and ADMINISTRATOR not in frappe.get_roles(frappe.session.user):
		user, default_user_filter = get_user_filters_by_role()
		filters["user"] = default_user_filter

	if filters.get("employee"):
		conditions += " and empatt.employee = " + '\'' + filters.get("employee") + '\''
	if filters.get("department"):
		conditions += " and tabEmp.department = " + '\'' + filters.get("department") + '\''
	if filters.get("from_date"):
		conditions += " and empatt.attendance_date >= " + '\'' + filters.get("from_date") + '\''
	if filters.get("to_date"):
		conditions += " and empatt.attendance_date<= " + '\'' + filters.get("to_date") + '\''
	if filters.get("user"):
		if filters.get("user") == ("Me"):
			userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
			if userId is not None:
				conditions += " and empatt.employee = " + '\'' + userId + '\''
		if filters.get("user") == ("Employee Reporting To Me"):
			userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
			if userId is not None:
				conditions += " and tabEmp.reports_to = " + '\'' + userId + '\''
		if filters.get("user") == "All Team":
			employee_list = get_auth_team_ids()
			if employee_list != "":
				conditions += " and empatt.employee in (" + employee_list + ")"
	else:
		userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
		if userId is not None:
			conditions += " and empatt.employee = " + '\'' + userId + '\''


	return conditions


def remove_tags(text):
	return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


@frappe.whitelist()
def getPaginationData(filters):
	filters = json.loads(filters)
	advances_list = get_conditions(filters)

	AuthRole = getAuthRole()
	employee_data, totalRecords = getLateAttendenceEmployees(advances_list, AuthRole, "")

	pagination = getPages(totalRecords, PAGE_SIZE)

	user, default_user_filter = get_user_filters_by_role()

	filtersData = {'user': user, 'pagination': pagination,'default_filter': default_user_filter, "totalRecords": totalRecords}
	return filtersData


def getLateAttendenceEmployees(advances_list ="",AuthRole ="",Limit ="",employee_id = None):

	# If Its an Employee show him only his attendence
	user = get_user_role()
	if user == EMPLOYEE:
		userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
		if userId is not None:
			advances_list += " and empatt.employee = " + '\'' + userId + '\''

	advances_list += " group by tabEmp.employee"

	advances_list += Limit

	select = """SELECT 
	    empatt.employee AS employeeID,
	    tabEmp.employee_name AS EmployeeName,
	    IF(tabEmp2.employee_name IS NULL,
		"-", tabEmp2.employee_name) As ReportingManager,
	    tabEmp.sub_department AS sub_department,
	    tabEmp.department AS Department,
	    count(empatt.late_arrival) as LateArrivalInstance,
    	sum(empatt.late_arrival) as TotalLateArrivalMinutes """


	employee_data = frappe.db.sql(select+"""
	         FROM
    `tabAttendance` empatt
		LEFT JOIN 
	`tabRoster Status` eas ON eas.name = empatt.attendance_status
        INNER JOIN
    `tabEmployee` AS tabEmp ON empatt.employee = tabEmp.employee 
         LEFT JOIN
    `tabEmployee` AS tabEmp2 ON tabEmp.reports_to = tabEmp2.employee

WHERE
	eas.consider_penalty = 1
    AND empatt.late_arrival > 0
    AND empatt.docstatus = 1
	          """ + advances_list, as_dict=True
								  )


	return employee_data,len(employee_data)

def getAuthRole():

    roleIs = ""
    AuthRole = frappe.get_roles(frappe.session.user)
    EmployeeList = ['Employee', 'All', 'Guest']
    if AuthRole == EmployeeList:
        roleIs = "Employee"
    else:
        roleIs = "Admin"

    return roleIs

def getPages(totalRecords,pageSize):
    pagination = ["1"]
    if pageSize > 0 and totalRecords > 1:
        totalPages = (totalRecords * 1.0)/pageSize
        totalPages = int(math.ceil(totalPages))
        pagination = range(1, totalPages+1)

    return pagination

def late_arrival_pop(late_arrival,emp_id):
	return """<a href='javascript:;' class="late-attendance-popup pull-right" onclick='get_late_arrival(this, "{1}")'>{0}</a>""".format(late_arrival, emp_id)

@frappe.whitelist()
def getPopUpData(employee_id,filters):
	filters = json.loads(filters)
	advances_list = get_conditions(filters)
	employeeData = getLateAttendenceEmployeesDetails(advances_list, "", "", employee_id)

	return employeeData

def getLateAttendenceEmployeesDetails(advances_list ="",AuthRole ="",Limit ="",employee_id = None):
	if employee_id is not None:
		advances_list += " and empatt.employee = " + '\'' + employee_id + '\''
        advances_list += " GROUP BY empatt.employee, empatt.attendance_date "
	select = """SELECT
					empatt.employee AS employeeID,
					tabEmp.employee_name AS EmployeeName,
					  empatt.attendance_date as attendanceDate,
					LEFT(DAYNAME(empatt.attendance_date),3) as dayName,
					IF(empatt.attendance_status IS NULL,
					"-", empatt.attendance_status)AS employee_shift,
					empatt.check_in AS checkIn,
					IF(DATE_FORMAT(empatt.check_out, '%Y-%m-%d %H:%i:%s') IS NULL,
					"-", DATE_FORMAT(empatt.check_out, '%Y-%m-%d %H:%i:%s'))AS checkOut,
					IF(empatt.late_arrival IS NULL,
					"-", empatt.late_arrival)AS LateArrivalMinutes,
					IF(empatt.left_early IS NULL,
					"-", IF(empatt.left_early < 0, "-",empatt.left_early))AS leftEarly,
					IF(empatt.working_hours IS NULL,
					"-", round(empatt.working_hours,2))AS workingHrs,
					IF(ats.color is null,'#428b46',ats.color) as color,
                   IF(lvapp.status IS NULL,'-',IF(COUNT(lvapp.leave_type) > 1, "Multiple Leaves Applied", CONCAT(lvapp.status,'-',lvapp.leave_type))) AS LeaveStatus
                      
                     """

	employee_data = frappe.db.sql(select + """
		         FROM
	    `tabAttendance` empatt
			LEFT JOIN 
		`tabRoster Status` eas ON eas.name = empatt.attendance_status
			INNER JOIN
	    `tabEmployee` AS tabEmp ON empatt.employee = tabEmp.employee 
	    	LEFT JOIN 
	    `tabRoster Status` ats ON ats.name = empatt.attendance_status
	         LEFT JOIN
	    `tabEmployee` AS tabEmp2 ON tabEmp.reports_to = tabEmp2.employee
	    	LEFT JOIN 
	        `tabLeave Application` as lvapp ON empatt.employee = lvapp.employee 
			And empatt.attendance_date between lvapp.from_date and lvapp.to_date 
			AND lvapp.docstatus < 2
	WHERE
		eas.consider_penalty = 1
	    AND empatt.late_arrival > 0
	    AND empatt.docstatus = 1
		          """ + advances_list, as_dict=True
								  )

	return employee_data, len(employee_data)