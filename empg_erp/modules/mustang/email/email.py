import frappe
import json
from frappe.utils.background_jobs import enqueue
from frappe import _
from frappe.utils import (format_time, get_link_to_form, get_url_to_report,
	global_date_format, now, now_datetime, validate_email_add)


def get_html_table_override(self, columns=None, data=None):
    date_time = global_date_format(now()) + ' ' + format_time(now())
    report_doctype = frappe.db.get_value('Report', self.report, 'ref_doctype')

    return frappe.render_template('empg_erp/templates/emails/auto_email_report.html', {
        'title': self.name,
        'description': self.description,
        'date_time': date_time,
        'columns': columns,
        'data': data,
        'report_url': get_url_to_report(self.report, self.report_type, report_doctype),
        'report_name': self.report,
        'edit_report_settings': ''
    })