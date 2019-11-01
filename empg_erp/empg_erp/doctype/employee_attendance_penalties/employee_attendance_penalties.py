# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from empg_erp.utils import copy_fields

class EmployeeAttendancePenalties(Document):
	
	def on_trash(self):
    		
		try:
			penalty_data_log = frappe.get_doc({"doctype": "Employee Attendance Penalties Log"})

			copy_fields(
				penalty_data_log, self, 
				["year", "month", "employee", "value", "instance", "penalty", "attendance_policy_rules", "type", "comments"]
			)
			penalty_data_log.created_by = frappe.session.user
			penalty_data_log.modified_by = frappe.session.user

			penalty_data_log.insert()

		except Exception as err:
			frappe.log_error(err)
			frappe.throw("unable to log penalty reversal")

			