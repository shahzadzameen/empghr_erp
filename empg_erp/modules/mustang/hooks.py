# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

website_context = {
	 "splash_image": "assets/empg_erp/mustang/images/erp-icon.png"
}


app_include_js = ["/assets/js/empg_erp.mustang.min.js"]

web_include_js = ["/assets/js/empg_erp.mustang.min.js"]

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "empg_erp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "empg_erp.install.before_install"
# after_install = "empg_erp.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "empg_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events	

doc_events = {
	"Leave Application": {
		"validate" : "empg_erp.modules.mustang.leave_application.leave_application.validate_override",
		"before_save" : "empg_erp.modules.mustang.leave_application.leave_application.before_save_override"
	},
	"Attendance" : {
		"before_save" : "empg_erp.modules.mustang.attendance.employee_attendance.before_save_attendance",
		"before_insert" : "empg_erp.modules.mustang.attendance.employee_attendance.before_save_attendance",
		"on_submit" : "empg_erp.modules.mustang.attendance.employee_attendance.on_submit",
		"before_submit" : "empg_erp.modules.mustang.attendance.employee_attendance.before_submit_attendance"
	},
	"Employee" : {
		"before_save" : "empg_erp.modules.mustang.employee.employee.before_save_hook",
		"after_insert" : "empg_erp.modules.mustang.employee.employee.after_insert_hook",
	},
	"Holiday List" : {
		"on_update" : "empg_erp.modules.mustang.attendance.employee_attendance.update_holiday_employee",
		"before_save" : "empg_erp.modules.mustang.attendance.employee_attendance.before_save_holiday_list",
	}
	
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"empg_erp.tasks.all"
	# ],
	# "daily": [
	# 	"empg_erp.modules.mustang.employee.generate_monthly"
	# ],
	# "hourly": [
	# 	"empg_erp.tasks.hourly"
	# ],
	# "weekly": [
	# 	"empg_erp.tasks.weekly"
	# ]
	# "monthly": [
	# 	"empg_erp.tasks.monthly"
	# ]

	"cron" : {
		# run daily at 11 p.m
		"0 23 * * *" : [
			"empg_erp.modules.mustang.employee.generate_monthly"
		]
	}
}

# Testing
# -------

# before_tests = "empg_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.core.doctype.user_permission.user_permission.get_user_permissions": "empg_erp.empg_erp.controller.user_permission.get_user_permissions"
# }


fixtures = ["Data Migration Plan", "Data Migration Connector", "Data Migration Mapping"]
override_whitelisted_methods = {
	"erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days": "empg_erp.modules.mustang.leave_application.leave_application.get_number_of_leave_days",
 	"erpnext.hr.doctype.leave_application.leave_application.get_holidays": "empg_erp.modules.mustang.leave_application.leave_application.get_holidays",
	"erpnext.hr.doctype.attendance.attendance.get_events": "empg_erp.modules.mustang.attendance.attendance_calendar.get_events"
}
