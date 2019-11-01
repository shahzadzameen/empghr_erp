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

# include js, css files in header of desk.html
app_include_css = ["/assets/css/empg_erp.min.css"]
app_include_js = ["/assets/js/empg_erp.min.js"]

# include js, css files in header of web template
# web_include_css = "/assets/empg_erp/css/empg_erp.css"
web_include_js = ["/assets/js/empg_erp.min.js"]

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
    "Leave Policy": {
        "autoname": "empg_erp.modules.common.leave_policy.leave_policy_autoname"
    },
    "User": {
		"after_insert" : "empg_erp.modules.common.desktop_icon.desktop_icon.hide_icons"
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


fixtures = ["Custom Script","Property Setter", "Custom Field", "Module Def","Widget","Widget Report","Bookmark", "Website Theme", "Role", "Report"]
override_whitelisted_methods = {
	"erpnext.hr.doctype.leave_application.leave_application.get_events": "empg_erp.modules.common.leave_application.get_events",
    "erpnext.hr.doctype.leave_application.leave_application.get_leave_details": "empg_erp.modules.mustang.leave_application.leave_application.get_leave_details",
 	"erpnext.hr.doctype.leave_application.leave_application.get_leave_approver": "empg_erp.modules.mustang.leave_application.leave_application.get_leave_approver",
    "frappe.desk.reportview.get" : "empg_erp.modules.common.get"
   }