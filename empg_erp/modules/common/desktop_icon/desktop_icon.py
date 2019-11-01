import frappe
from empg_erp.modules.common.error_handler import ErrorHandler
from frappe.desk.doctype.desktop_icon.desktop_icon import update_icons
from frappe.desk.doctype.desktop_icon.desktop_icon import get_all_icons
from empg_erp.utils import get_site_path, get_desktop_icons_list, custom_query_report_icons

def hide_icons(doctype,event_name):
	'''
	Hiding all standard icons except those which we defined for Employee 
	'''
	blocked_module = ['Help', 'Website', 'Learn', 'Contacts', 'Tools']
	try:
		site_dir = get_site_path()
		desktop_icons_list = get_desktop_icons_list(site_dir)
		hide_list = list(set(get_all_icons()) - set(desktop_icons_list))
		update_icons(hide_list, doctype.email)
		for report_list in custom_query_report_icons(site_dir):
			if frappe.db.exists('Desktop Icon', {"owner": doctype.email, "module_name": report_list}):
				desktop_icon = frappe.get_doc('Desktop Icon', {"owner": doctype.email, "module_name": report_list})
				desktop_icon._report = report_list
				desktop_icon.save()
		for block_module in blocked_module:
			if frappe.db.exists('Desktop Icon', {"owner": doctype.email, "module_name": block_module}):
				blocked_doc = frappe.get_doc('Desktop Icon', {"owner": doctype.email, 'module_name': block_module})
				blocked_doc.blocked = 1
				blocked_doc.save()
	except Exception as err:
		ErrorHandler.log_error(str(err))