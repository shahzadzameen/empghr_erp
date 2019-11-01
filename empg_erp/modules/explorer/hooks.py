# -*- coding: utf-8 -*-
from __future__ import unicode_literals


website_context = {
	 "splash_image": "assets/empg_erp/explorer/images/erp-icon.png"
}
# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------



app_include_js = ["/assets/js/empg_erp.explorer.min.js"]

web_include_js = ["/assets/js/empg_erp.explorer.min.js"]

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
	# "Employee": {
	# 	"validate" : "empg_erp.empg_erp.controller.employee.update_reports_to"
	# },
	"Leave Application": {
		"validate" : "empg_erp.modules.explorer.leave_application.leave_application.validate_override"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"empg_erp.tasks.all"
# 	],
# 	"daily": [
# 		"empg_erp.tasks.daily"
# 	],
# 	"hourly": [
# 		"empg_erp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"empg_erp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"empg_erp.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "empg_erp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.core.doctype.user_permission.user_permission.get_user_permissions": "empg_erp.empg_erp.controller.user_permission.get_user_permissions"
# }
