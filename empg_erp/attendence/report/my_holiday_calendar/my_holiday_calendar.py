# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from empg_erp.constants.globals import PAGE_SIZE
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
import frappe
import json
import math

def execute(filters=None):
	columns, data = [], []
	advances_list = ""
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

	user_id = frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user_id}, "employee")
	holiday_data,totalRecords = get_emp_holidays(advances_list,employee,Limit)

	for hl in holiday_data:
		row = []
		row.append(hl.description)
		row.append(hl.holiday_date)


		data.append(row)

	columns = [("Name<input type='hidden' value='"+limit+"' id='page' />") + "::300", ("Date")+":Date:220"]

	return columns, data

def get_emp_holidays(advances_list,emp_id,Limit = ""):
	holiday_list_data = []
	holiday_list = get_holiday_list_for_employee(emp_id)

	if holiday_list:
		advances_list += Limit
		holiday_list_data = frappe.db.sql("""
		Select * from `tabHoliday` 
		Where parent = '{0}'
		ORDER BY holiday_date ASC """.format(holiday_list)+advances_list,as_dict=True)


	return holiday_list_data,len(holiday_list_data)

@frappe.whitelist()
def getPaginationData(filters):

	filters = json.loads(filters)

	user_id = frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user_id}, "employee")
	holiday_data,totalRecords = get_emp_holidays("", employee, "")

	filtersData = {"totalRecords": totalRecords}
	return filtersData

