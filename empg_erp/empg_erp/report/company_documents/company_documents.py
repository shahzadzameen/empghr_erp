# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from empg_erp.constants.globals import PAGE_SIZE,LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR,EMPLOYEE, DOCUMENTS_EXT_ICONS
from empg_erp.utils import get_user_role,get_auth_team_ids,get_user_filters_by_role
import xml
import json
import frappe
import math
import os
from pypika import Query, Tables, Table,Field, JoinType, functions as fn, Case, Order


def execute(filters={}):
	query_obj = Query.from_(PD)
	query_obj = get_conditions(filters,query_obj)
	_roster_employee = []
	columns = []

	if filters.get("page"):
		concat = str(filters.get("page")).split('_')
		limit = str(concat[0])
	else:
		limit = str(PAGE_SIZE)

	AuthRole = getAuthRole()
	documents_data = getPolicyDocuments(query_obj, AuthRole, limit)

	limit = str(filters.get("page"))
	if limit == 'None':
		limit = str(PAGE_SIZE)

	for document in documents_data:
		_roster_employee.append(report_row(document))

	columns = [("These may be useful<input type='hidden' value='" + limit + "' id='page' />") + "::1110"]
	return columns, _roster_employee

PD = Table('tabPolicy Document')

def get_conditions(filters, query_obj=Query.from_(PD)):

	if filters.get("Policy_Document_Category"):
		query_obj = query_obj.where(PD.parent == filters.get("Policy_Document_Category"))
	else:
		if not (any(x in frappe.get_roles() for x in [HR_MANAGER, HR_USER, ADMINISTRATOR, LINE_MANAGER])):
			query_obj = query_obj.where(PD.parent != "Line Manager Guides")
		else:
			query_obj = query_obj

	return query_obj


def remove_tags(text):
	return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


@frappe.whitelist()
def getPaginationData(filters):
	filters = json.loads(filters)
	total_records = 0

	query_obj = get_conditions(filters)

	AuthRole = getAuthRole()
	att_count = getPolicyDocuments(query_obj=query_obj, AuthRole=AuthRole, return_count = True)

	if len(att_count) > 0:
		total_records = att_count[0]["total"]

	pagination = getPages(total_records, PAGE_SIZE)

	user, default_user_filter = get_user_filters_by_role()

	filtersData = {'user': user, 'pagination': pagination, 'default_filter': default_user_filter,
				   "totalRecords": total_records}
	return filtersData


def getPolicyDocuments(query_obj="", AuthRole="", Limit="", return_count = False):
	
	query_obj = query_obj.select(
			PD.title,
			PD.document
		).orderby(PD.title, order=Order.asc)

	if not return_count:
		query_obj = query_obj.limit(Limit)
	
	if return_count:
		query_obj = Query.from_(query_obj).select((fn.Count(0)).as_("total"))

	try:
		employee_data = frappe.db.sql(query_obj.get_sql(quote_char="`"), as_dict=True)
		return employee_data

	except:
		return []


def getAuthRole():
	roleIs = ""
	AuthRole = frappe.get_roles(frappe.session.user)
	EmployeeList = ['Employee', 'All', 'Guest']
	if AuthRole == EmployeeList:
		roleIs = "Employee"
	else:
		roleIs = "Admin"

	return roleIs


def getPages(totalRecords, pageSize):
	pagination = ["1"]
	if pageSize > 0 and totalRecords > 1:
		totalPages = (totalRecords * 1.0) / pageSize
		totalPages = int(math.ceil(totalPages))
		pagination = range(1, totalPages + 1)

	return pagination


def report_row(document):
	row = []

	filename_w_ext = os.path.basename(str(document.document))
	filename, file_extension = os.path.splitext(filename_w_ext)

	if file_extension and file_extension in DOCUMENTS_EXT_ICONS:
		row.append("<i class='" + DOCUMENTS_EXT_ICONS[file_extension] + " font-size-20'></i> <span class='doc-text-alignment'><a href='" + document.document + "' target='_blank'>" + str(
				document.title) + "</a></span>")
	else:
		row.append("<i class='" + DOCUMENTS_EXT_ICONS['.pdf'] + " font-size-20'></i> <span class='doc-text-alignment'><a href='" + document.document + "' target='_blank'>" + str(
			document.title) + "</a></span>")
	return row