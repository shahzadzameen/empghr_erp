# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _, _dict
from frappe.utils import (flt, cstr, getdate, get_first_day, get_last_day,
	add_months, add_days, formatdate)

from empg_erp.utils import (get_config_by_name, get_prioritized_role)
from widget_data import get_widget_data

@frappe.whitelist()
def get_widget(widget, _filter = None):
	widget = json.loads(widget)
	return get_widget_data(widget, _filter)

@frappe.whitelist()
def get_widget_name(_filter = None):
    
	result = frappe.db.sql("""
			SELECT depends_on, w.name, w.title, w.widget_wrapper_class, w.widget_position,
			group_concat(wf.filter) as filters, group_concat(wr.role) as roles
			FROM tabWidget w
			LEFT JOIN `tabWidget Filter` as wf on w.name = wf.parent
			LEFT JOIN `tabWidget Role` as wr on w.name = wr.parent
			WHERE disabled = 0
			GROUP BY w.name
			ORDER BY w.display_order ASC
	""", as_dict=True)

	response = []
	for data in result:
		get_active_widgets(data, response, frappe.get_roles(), _filter)

	return response


def get_active_widgets(data, response, user_roles, _filter = None):

	depends_on = None
	if data.depends_on is not None:
		depends_on = eval(data.depends_on)

	if data.depends_on is None or depends_on == 1:
		sql = frappe.get_all('Widget',
							 filters={'disabled': 0, 'name': data.name},
							 fields=['name', 'lower(type) as type', 'chart_type', 'title', 'width', 'height',
									 'background_color','widget_wrapper_class','widget_position'],
							 order_by='display_order'
							 )
		if sql:
			result = sql[0]

			if (( not _filter or not data["filters"] or ( _filter and _filter in data["filters"]))\
				and ( not data["roles"] or any(role in data["roles"] for role in user_roles) )):
				result["show_widget"] = True

				response.append(result)

			else:
				result["show_widget"] = False
	return response