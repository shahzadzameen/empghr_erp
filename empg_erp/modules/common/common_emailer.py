# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_site_base_path, get_url, random_string


@frappe.whitelist()
def send_welcome_mail_to_user():
    employees = frappe.get_all("Employee", filters={'status':'Active','user_id':("!=", "")}, fields=['user_id'])
    for employee in employees:
        user = frappe.get_doc("User", employee.user_id)

        if user and user.send_welcome_email != 1 and user.name != 'Administrator' and user.name != 'Guest':
            user.send_welcome_email = 1
            user.save()
            link = user.reset_password()
            subject = None
            method = frappe.get_hooks("welcome_email")
            if method:
                subject = frappe.get_attr(method[-1])()
            if not subject:
                site_name = frappe.db.get_default('site_name') or frappe.get_conf().get("site_name")
                if site_name:
                    subject = _("Welcome to {0}".format(site_name))

                else:
                    subject = _("Complete Registration")

            user.send_login_mail(subject, "new_user",
                                 dict(
                                     link=link,
                                     site_url=get_url(),
                                 )) 