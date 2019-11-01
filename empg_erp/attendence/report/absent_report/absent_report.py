# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from empg_erp.constants.globals import PAGE_SIZE,LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR,EMPLOYEE
from empg_erp.utils import get_user_role
from empg_erp.utils import get_auth_team_ids,get_user_filters_by_role
import xml
from pprint import pprint

import frappe
import datetime
import calendar
import sys
import json
import math
from frappe import _



def execute(filters=None):
    if not filters: filters = {}


    advances_list = get_conditions(filters)
    _roster_employee = []
    columns = []

    AuthRole = getAuthRole()
    Limit =""

    if filters.get("page"):
        concat = str(filters.get("page")).split('_')
        limit = str(concat[0])
    else:
        limit = str(PAGE_SIZE)
    Limit = " LIMIT " + limit
    limit = str(filters.get("page"))
    if limit == 'None':
        limit = str(PAGE_SIZE)

    employee_data,dataLength = getAbsentEmployees(advances_list,AuthRole,Limit)
    for emp in employee_data:
        row = []
        row.append(emp.employeeID)
        row.append(emp.EmployeeName)
        row.append(emp.AttendenceDate)
        row.append(emp.theDayName)
        row.append(emp.Department)

        leave_type = '-'
        if emp.leave_application_type is not None:
            if emp.leave_application_type != 'Multiple Leaves Applied' and emp.LeaveStatus is not None:
                leave_type = "{0}-{1}".format(emp.LeaveStatus, emp.leave_application_type)
            else:
                leave_type = emp.leave_application_type

        row.append(leave_type)
        row.append(emp.description)


        if emp.ApproverComments is not None:
            row.append(str(emp.ApproverComments))
        else:
            row.append("")
        _roster_employee.append(row)

    columns = [("Code")+ "::140",("Employee")+ "::140",("Date")+ ":Date:100",("Day")+ "::40",("Department")+ "::160",("Leave Status")+ "::160",("Reason")+ "::230", ("Comments<input type='hidden' value='"+limit+"' id='page' />") + "::230"]
    return columns, _roster_employee

def get_conditions(filters):
        conditions = ""

        # if user filter has not assigned on page load and its not 'Administrator' then assign 'Me' by default
        if filters.get("user") is None and ADMINISTRATOR not in frappe.get_roles(frappe.session.user):
            user, default_user_filter = get_user_filters_by_role()
            filters["user"] = default_user_filter

        if filters.get("employee"):
            conditions += " and empatt.employee = "+'\''+filters.get("employee")+'\''
        if filters.get("department"):
            conditions += " and tabEmp.department = "+'\''+filters.get("department")+'\''
        if filters.get("from_date"):
            conditions += " and empatt.attendance_date >= "+'\''+filters.get("from_date")+'\''
        if filters.get("to_date"):
            conditions += " and empatt.attendance_date<= "+'\''+filters.get("to_date")+'\''
        if filters.get("company"):
            conditions += " and empatt.company = " + '\'' + filters.get("company") + '\''
        if filters.get("user"):
            if filters.get("user") == "Me":
                userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
                if userId is not None:
                    conditions += " and empatt.employee = " + '\'' + userId + '\''
            if filters.get("user") == "Employee Reporting To Me":
                userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
                if userId is not None:
                    conditions += " and tabEmp.reports_to = " + '\'' + userId + '\''
            if filters.get("user") == "All Team":
                employee_list = get_auth_team_ids()
                if employee_list != "":
                     conditions += " and empatt.employee in ("+employee_list+")"

        return conditions

def remove_tags(text):
    return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


@frappe.whitelist()
def getPaginationData(filters):
    filters = json.loads(filters)

    advances_list = get_conditions(filters)
    AuthRole = getAuthRole()
    employee_data, totalRecords = getAbsentEmployees(advances_list, AuthRole,"")


    pagination = getPages(totalRecords, PAGE_SIZE)

    user,default_user_filter = get_user_filters_by_role()


    filtersData = {'user': user, 'pagination': pagination,'default_filter': default_user_filter,"totalRecords": totalRecords }

    return filtersData


def getAbsentEmployees(advances_list,AuthRole,Limit):


    # If Its an Employee show him only his AbsentReport
    user = get_user_role()
    if user == EMPLOYEE:
        userId = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
        if userId is not None:
            advances_list += " and empatt.employee = " + '\'' + userId + '\''

    advances_list += " GROUP BY empatt.employee, empatt.attendance_date "
    advances_list += " ORDER BY empatt.attendance_date DESC "
    advances_list += Limit

    employee_data = frappe.db.sql("""
          SELECT 
    tabEmp.employee_name AS EmployeeName,
    empatt.employee AS employeeID,
    tabEmp.department AS Department,
    lvapp_prv.status AS LeaveStatus,
    IF(lvapp_prv.leave_type IS NULL
            AND empatt.check_out IS NULL
            AND empatt.check_in IS NULL
            AND empatt.attendance_status = 'On',
        'Not Applied',
        IF(COUNT(lvapp_prv.leave_type) > 1,
            'Multiple Leaves Applied',
            lvapp_prv.leave_type)) AS leave_application_type,
    IF(lvapp.name IS NULL,
            lvapp_prv.leave_approver_comments,
        lvapp.leave_approver_comments) AS ApproverComments,
    empatt.attendance_date AS AttendenceDate,
    IF(lvapp.name IS NULL,lvapp_prv.description,
        lvapp.description) AS description,
    LEFT(DAYNAME(empatt.attendance_date), 3) AS theDayName
FROM
    `tabAttendance` empatt
        LEFT JOIN
    `tabRoster Status` eas ON eas.name = empatt.attendance_status
        LEFT JOIN
    `tabLeave Application` AS lvapp_prv ON (empatt.employee = lvapp_prv.employee)
        AND (empatt.attendance_date BETWEEN lvapp_prv.from_date AND lvapp_prv.to_date)
        AND lvapp_prv.docstatus < 2
        LEFT OUTER JOIN
    `tabLeave Application` AS lvapp ON (empatt.employee = lvapp.employee
        AND (lvapp.creation > lvapp_prv.creation))
        AND (empatt.attendance_date BETWEEN lvapp.from_date AND lvapp.to_date)
        AND lvapp.docstatus < 2
        INNER JOIN
    `tabEmployee` AS tabEmp ON empatt.employee = tabEmp.employee
WHERE
    eas.consider_absent = 1
        AND empatt.attendance_date <= DATE(NOW())
        AND empatt.docstatus = 1
        AND empatt.check_in is NULL AND empatt.check_out is NULL
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