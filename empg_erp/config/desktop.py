# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _
from empg_erp.utils import get_site_path
from empg_erp.constants.globals import LINE_MANAGER_GUIDES


def desktop_list(site_dir):
	desktop_list = {
		"mustang": [
				{
					"module_name": "Daily Attendance Report",
					"color": "#9b59b6",
					"icon": "fa fa-clock-o",
					"type": "link",
					"link": "query-report/Daily Attendance Report",
					"_report": "Daily Attendance Report",
					"label": _("Daily Attendance Report")
				},
				{
					"module_name": "Absent Report",
					"color": "#83C21E",
					"icon": "fa fa-calendar-minus-o",
					"type": "link",
					"link": "query-report/Absent Report",
					"_report": "Absent Report",
					"label": _("Absent Report")
				},
				{
					"module_name": "Late Attendance Report",
					"color": "#C0392B",
					"icon": "octicon octicon-watch",
					"type": "link",
					"link": "query-report/Late Attendance Report",
					"_report": "Late Attendance Report",
					"label": _("Late Attendance Report")
				},
				{
					"module_name": "Attendance Request",
					"color": "#2ecc71",
					"icon": "fa fa-plus-square",
					"type": "link",
					"link": "List/Attendance Request/List",
					"_doctype": "Attendance Request",
					"label": _("Attendance Request")
				},
				{
					"module_name": "Policy Document Category",
					"color": "#429ca0",
					"icon": "fa fa-gavel",
					"type": "link",
					"link": "List/Policy Document Category/List",
					"_doctype": "Policy Document Category",
					"label": _("Policy Documents")
				}
		],
		"explorer": [
			{
				"module_name": "Appraisal",
				"color": "#8f2ecc",
				"icon": "fa fa-thumbs-up",
				"type": "link",
				"link": "List/Appraisal/List",
				"_doctype": "Appraisal",
				"label": _("Performance Reviews")
			},
			{
				"module_name": "Company Documents",
				"color": "#429ca0",
				"icon": "fa fa-gavel",
				"type": "link",
				"link": "query-report/Company Documents?document_type={}".format(LINE_MANAGER_GUIDES),
				"_report": "Company Documents",
				"label": _("Company Documents")
			},
			{
				"module_name": "e-HR Employees",
				"color": "#E9AB17",
				"icon": "fa fa-sitemap",
				"type": "page",
				"link": "e-hr-employees",
				"label": _("e-HR Employees")
			},
			{
				"module_name": "Letter Request",
				"color": "#93c572",
				"icon": "fa fa-envelope-square",
				"type": "link",
				"link": "List/Letter Request/List",
				"_doctype": "Letter Request",
				"label": _("Request Management")
			},
			{
				"module_name": "Refer a Friend",
				"color": "#647B80",
				"icon": "fa fa-user-plus",
				"type": "link",
				"link": "List/Refer a Friend/List",
				"_doctype": "Refer a Friend",
				"label": _("Refer a Friend")
			},
			{
				"module_name": "Expense Claim",
				"color": "#2ecc71",
				"icon": "fa fa-money",
				"type": "link",
				"link": "List/Expense Claim/List",
				"_doctype": "Expense Claim",
				"label": _("Expense Claim")
			}
		]
	}
	return desktop_list[site_dir]


def get_data():
	icon_list = [
		{
			"module_name": "Widgets",
			"color": "#f4a142",
			"icon": "octicon octicon-device-desktop",
			"type": "module",
			"link": "dashboard",
			"label": _("Dashboard")
		},
		{
			"module_name": "EMPG-ERP",
			"color": "#2ecc71",
			"icon": "octicon octicon-home",
			"type": "module",
			"label": _("EMPG-ERP")
		},
		{
			"module_name": "EMPG Employee",
			"color": "#3498db",
			"icon": "octicon octicon-gear",
			"type": "module",
			"label": _("Employee Settings")
		},
		{
			"module_name": "Leave Application",
			"color": "#2ecc71",
			"icon": "fa fa-sign-out",
			"type": "link",
			"link": "List/Leave Application/List",
			"_doctype": "Leave Application",
			"label": _("Leave Application")
		},
		{
			"module_name": "Announcement",
			"color": "#4e1e1e",
			"icon": "fa fa-bullhorn",
			"type": "link",
			"link": "List/Announcement/List",
			"_doctype": "Announcement",
			"label": _("Announcement")
		},
		{
			"module_name": "Employee Leave Balance",
			"color": "#FFF5A7",
			"icon": "octicon octicon-calendar",
			"type": "link",
			"link": "query-report/Employee Leave Balance",
			"_report": "Employee Leave Balance",
			"label": _("Employee Leave Balance")
		}
	]
	desk_icons = desktop_list(get_site_path())
	if desk_icons:
		for desk_icon in desk_icons:
			icon_list.append(desk_icon)
	return icon_list









