# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

def validate_new_leaves_allocated_value_override(doctype):
	"""validate that leave allocation is in multiples of 0.5"""
	pass


def get_leave_allocation_record(employee,type,from_date,to_date):
    alloted_leaves_record = frappe.db.sql("""
		select
			name,leave_type,total_leaves_allocated
		from `tabLeave Allocation`
		where employee = %(employee)s and leave_type = %(leave_type)s 
        and  to_date >= %(from_date)s and from_date <= %(to_date)s and docstatus = 1""", {
			"employee": employee,
			"from_date": from_date,
			"to_date": to_date,
            "leave_type": type
		}, as_dict = 1)

    return alloted_leaves_record

def	validate_period_override(doctype):
	"""validate that leave allocation period greater than 0"""
	from frappe.utils import date_diff
	if date_diff(doctype.to_date, doctype.from_date) < 0:
		frappe.throw(_("To date cannot be before from date"))