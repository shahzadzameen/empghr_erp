import frappe
from frappe import _
from frappe.desk.doctype.bulk_update.bulk_update import show_progress
from frappe.desk.form.load import get_docinfo, run_onload
from empg_erp.modules.common.error_handler import ErrorHandler
from frappe.email.doctype.notification.notification import Notification
from erpnext.hr.doctype.appraisal.appraisal import Appraisal
from empg_erp.modules.common.appraisal.appraisal import validate_overide
from empg_erp.modules.common.department import autoname_override, before_rename_override
from erpnext.hr.doctype.department.department import Department
from empg_erp.constants.globals import USER, USER_BULK_UPDATE_RESTRICTED_FIELDS, EMPLOYEE, EMPLOYEE_BULK_UPDATE_RESTRICTED_FIELDS, LINE_MANAGER,ADMINISTRATOR, BLOCK_BULK_UPDATE, HR_MANAGER, HR_USER
from empg_erp.utils import get_user_role, get_auth_team_ids, get_employee_code,check_advance_privilege_by_name,get_config_by_name
from datetime import datetime
from frappe.desk.reportview import compress, execute, get_form_params
from empg_erp.utils import get_site_path

# import numpy as np

Department.autoname = autoname_override
Department.before_rename = before_rename_override
# Appraisal.validate = validate_overide

@frappe.whitelist()
def check_is_edit(employee=""):
	login_empcode = get_employee_code()
	if not (any(x in frappe.get_roles() for x in [HR_MANAGER, HR_USER, ADMINISTRATOR])):
		team_ids = get_auth_team_ids(True)
		try:
			team_ids.remove(login_empcode)
		except ValueError:
			pass
		if employee in team_ids:
			response = {"disabled": True}
		else:
			response = {"disabled": False}
	else:
		response = {"disabled": False}
	if employee == login_empcode:
		response = {"disabled": True, "shift_type": True}

	return response


# That function is override from reportview file
@frappe.whitelist()
@frappe.read_only()
def get():
	args = get_form_params()

	try:
		args["filters"] = args["filters"] + frappe.get_doc({"doctype" : "Doctype List Rules", "doc" : args["doctype"]}).get_filters()
	except Exception as err:
		frappe.log_error(err)

	# OVERRIDE START HERE
	# Show only custom reports which are defined in array
	role = get_user_role()
	report_list = get_config_by_name('COMMON_REPORT_ALLOWED') + get_config_by_name('REPORTS_ALLOWED_LIST')
	if args['doctype'] == 'Report':
		if role is not ADMINISTRATOR:
			args['filters'].append(['Report', 'disabled', '=', 0])
			args['page_length'] = 500
	results = execute(**args)
	exec_arr = []
	if args['doctype'] == 'Report':
		if role is not ADMINISTRATOR:
			for result in results:
				if result.name in report_list:
					exec_arr.append(result)
				elif 'total_count' in result:
					exec_arr.append(result)
		else:
			exec_arr = results
	else:
		exec_arr = results
	# OVERRIDE END HERE
	
	data = compress(exec_arr, args=args)
	return data