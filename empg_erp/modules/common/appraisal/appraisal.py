import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from erpnext.hr.doctype.appraisal.appraisal import fetch_appraisal_template
from empg_erp.constants.globals import LINE_MANAGER, ADMINISTRATOR, HR_MANAGER, EMPLOYEE
from empg_erp.utils import get_user_role, get_employee_code, get_report_to
from erpnext.hr.utils import set_employee_name
from frappe.utils import flt, getdate, formatdate
import datetime
from empg_erp.modules.common.error_handler import ErrorHandler

@frappe.whitelist()
def is_self_rated(name):
	try:
		return frappe.db.get_value("Appraisal Template",
					{"name": name},
					["self_rating_allowed"])
	except Exception as err:
		ErrorHandler.log_error(str(err))
		frappe.throw(("Error: {}".format(err)))


@frappe.whitelist()
def get_employee_details(employee):
	try:
		joining, emp_type =  frappe.db.get_value("Employee",
					{"employee": employee},
					["date_of_joining","employment_type"])
		return {"joining":frappe.utils.formatdate(joining), "emp_type": emp_type}
	except Exception as err:
		ErrorHandler.log_error(str(err))
		frappe.throw(("Error: {}".format(err)))

@frappe.whitelist()
def fetch_appraisal_template(source_name, target_doc=None):
	target_doc = get_mapped_doc("Appraisal Template", source_name, {
		"Appraisal Template": {
			"doctype": "Appraisal",
		},
		"Appraisal Template Goal": {
			"doctype": "Appraisal Goal",
		},
		"Appraisal Template Goals Boolean": {
			"doctype": "Appraisal Goals Boolean",
		},
		"Appraisal Template Goals Questions": {
			"doctype": "Appraisal Goals Questions",
		}
	}, target_doc)
	return target_doc

@frappe.whitelist()
def can_add_appraisal_score(employee):
	# only his own line manager can chanage manager's rating
	user_role = get_user_role()
	if(user_role == ADMINISTRATOR or user_role == HR_MANAGER):
		return True
	if(get_employee_code() == get_report_to(employee)):
		if(user_role == LINE_MANAGER and type(employee) !="undefined" and employee != get_employee_code()):
			return True
	else:
		return False

@frappe.whitelist()
def isEmployeeAllowed(employee):
	if(type(employee) !="undefined" and employee == get_employee_code()):
		return False
	else:
		return True

@frappe.whitelist()
def validate_due_days(employee,kra_template):
	try:
		joining = frappe.db.get_value("Employee",
				{"name": employee},
				["date_of_joining"])
		today = datetime.date.today()
		diff = today - joining
		due_days= frappe.db.get_value("Appraisal Template",
					{"name": kra_template},
					["appraisal_due_days"])

		if(due_days > diff.days):
			return False
		return True
	except Exception as err:
		ErrorHandler.log_error(str(err))
		frappe.throw(("Error: {}".format(err)))

def validate_overide(self):
	if not self.status:
		self.status = "Draft"

	set_employee_name(self)
	validate_dates(self)
	calculate_total_override(self)

def validate_dates(self):
	if getdate(self.start_date) > getdate(self.end_date):
		frappe.throw(_("End Date can not be less than Start Date"))

def calculate_total_override(self):
	total, total_w  = 0, 0
	for d in self.get('goals'):
		if d.score:
			d.score_earned = flt(d.score) * flt(d.per_weightage) / 100
			total = total + d.score_earned
		total_w += flt(d.per_weightage)
	
	#Override begin
	if int(total_w) != 100:
		if int(total_w) == 0:
			pass
		else:
			frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))
	#Override Ends

	self.total_score = total


@frappe.whitelist()
def refusal_reason(document_name, reason=""):
	try:
		data = frappe.get_doc("Appraisal", document_name)
		data.reason_for_refusal = reason
		data.save()
	except Exception as err:
		ErrorHandler.log_error(str(err))
		frappe.throw(("Error: {}".format(err)))

@frappe.whitelist()
def my_reporting_manager(employee):
	if (get_employee_code() == get_report_to(employee)):
		return True
	return False

