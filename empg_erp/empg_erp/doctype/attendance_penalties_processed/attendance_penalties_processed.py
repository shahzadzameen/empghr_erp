# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE
from empg_erp.utils import copy_fields
from datetime import datetime

class AttendancePenaltiesProcessed(Document):
    	
	def remove_penalty_leaves(self):
		
		try:

			penalty_leaves_list = frappe.get_list(
				"Employee Penalty Leaves", 
				filters = {"attendance_penalties_processed" : self.name},
				fields = ["name"]
				)

			if len(penalty_leaves_list) > 0:
    				
				for penalty_leave in penalty_leaves_list:
					frappe.get_doc("Employee Penalty Leaves",penalty_leave["name"]).cancel()

		except Exception as err:
			frappe.log_error(err)
			frappe.throw("unable to revert penalty leaves")

    		
	def remove_penalty_processed(self):

		try:

			processed_data_log = frappe.get_doc({"doctype": "Attendance Penalties Processed Log"})

			copy_fields(processed_data_log, self, ["month", "year", "employee"])
			processed_data_log.created_by = frappe.session.user
			processed_data_log.modified_by = frappe.session.user

			processed_data_log.insert()

		except Exception as err:
			frappe.log_error(err)
			frappe.throw("unable to update penalty reversal")


	def on_trash(self):
    		

		self.remove_penalty_leaves()
		self.remove_penalty_processed()


def check_processed(employee, month, year, attendance_date):
    	
	_today = datetime.strptime(str(attendance_date), "%Y-%m-%d")
	_cutoff_date = datetime(_today.year, _today.month, MONTHLY_ATTENDANCE_DATE)

	if _today > _cutoff_date:
		month = int(month) + 1
	
	attendace_processed = frappe.db.get_value(
		"Attendance Penalties Processed",
			filters = {
				"employee": employee,
				"month": month,
				"year": year
			}
		)

	if(attendace_processed != None):
		return True
	
	return False

