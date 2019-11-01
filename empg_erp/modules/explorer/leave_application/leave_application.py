# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from frappe import _
from empg_erp.modules.common.leave_application import validate_leave_approver

def validate_override(doctype,event_name):
	validate_leave_approver(doctype)
