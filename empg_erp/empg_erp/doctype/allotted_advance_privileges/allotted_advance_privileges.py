# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AllottedAdvancePrivileges(Document):
	def on_update(self):
    	# TODO : import function delete_cache_by_key from utils to delete cache
		frappe.cache().delete_key("advance_privileges")
	def after_delete(self):
		frappe.cache().delete_key("advance_privileges")

def get_privileges(employee=None, department=None, designation=None, company=None, roles=None):
	where_condition = get_conditions(employee, department, designation, company, roles)
	advance_privileges = frappe.db.sql("""
		SELECT 
			adv_priv.privilege
		FROM
			`tabAllotted Advance Privileges` AS adv_priv
		WHERE {} GROUP BY adv_priv.privilege""".format(where_condition),
		as_dict=True)

	return advance_privileges

def get_conditions(employee=None, department=None, designation=None, company=None, roles=None):
    	conditions = ""

	if employee is not None:
		conditions += " (adv_priv.type = 'Employee' AND adv_priv.privilege_to = '%(employee)s' )" % {"employee" : employee}
	if department is not None:
		conditions += " or (adv_priv.type = 'Department' AND adv_priv.privilege_to = '%(department)s' )" % {"department" : department}
	if designation is not None:
		conditions += " or (adv_priv.type = 'Designation' AND adv_priv.privilege_to = '%(designation)s' )" % {"designation" : designation}
	if company is not None:
		conditions += " or (adv_priv.type = 'Company' AND adv_priv.privilege_to = '%(company)s' )" % {"company" : company}
	if roles is not None:
		conditions += " or (adv_priv.type = 'Role' AND adv_priv.privilege_to IN  ( %(roles)s) )" % {"roles" : ','.join('\'{0}\''.format(role) for role in roles)}
	return conditions

def get_advance_privileges():
	employee_privileges = []
	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "employee")
	employee_roles = frappe.get_roles(frappe.session.user)
	employee_object = frappe.db.get_value("Employee",employee,["employee", "department","designation","company"])

	if(employee_object and employee_roles):
		allPrivileges = get_privileges(employee_object[0],employee_object[1],employee_object[2],employee_object[3], employee_roles)
		if(allPrivileges):
			for priv in allPrivileges:
				employee_privileges.append(priv.privilege)

	return employee_privileges

