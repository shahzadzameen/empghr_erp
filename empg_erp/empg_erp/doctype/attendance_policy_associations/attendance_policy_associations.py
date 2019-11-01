# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.model.document import Document
from empg_erp.constants.table_names import EMP_ATT_ASSOCIATION_BUFF, EMP_ATT_ASSOCIATION, \
ATT_POLICY_ASSOCIATION, ATT_POLICY
from empg_erp.utils import get_table_name

class AttendancePolicyAssociations(Document):
	def validate(self):
		if self.is_new():
			name = frappe.db.get_value('Attendance Policy Associations', {'object_type': self.object_type, 'object_id': self.object_id})
			if name is not None:
				throw(_("Policy Against Type '" + self.object_type + "' and ID '" + self.object_id + "' already exists."))
		else:
			name = frappe.db.get_value('Attendance Policy Associations', {'name': ('<>', self.name), 'object_type': self.object_type, 'object_id': self.object_id})
			if name is not None:
				throw(_("Policy Against Type '" + self.object_type + "' and ID '" + self.object_id + "' already exists."))
	
	def on_update(self):

		fill_associations()


def fill_associations():
	
	frappe.db.sql("""DELETE FROM `{0}` """.format(get_table_name(EMP_ATT_ASSOCIATION_BUFF)))

	frappe.db.sql("""SET @rownum = 0""")


	frappe.db.sql("""

		INSERT IGNORE INTO `{0}` (employee, attendance_policy, name, creation)
		SELECT e.employee, 
			IF(u.attendance_policy  IS NOT NULL, u.attendance_policy , 
				IF(pos.attendance_policy IS NOT NULL, pos.attendance_policy,
					IF(dep.attendance_policy IS NOT NULL, dep.attendance_policy,p.name	)
				)
			) AS attendance_policy,
			@rownum := @rownum + 1 as name,
			now() as creation
			FROM `tabEmployee` e
			LEFT JOIN `{1}` dep ON dep.object_id = e.`department` AND dep.object_type = 'Department'
			LEFT JOIN `{1}` pos ON pos.object_id = e.`job_title` AND pos.object_type = 'Job Title'
			LEFT JOIN `{1}` u ON u.object_id = e.`employee` AND u.object_type = 'Employee'
			LEFT JOIN `{2}` p ON p.`is_default` = 1;
	""".format(
		get_table_name(EMP_ATT_ASSOCIATION_BUFF), 
		get_table_name(ATT_POLICY_ASSOCIATION),
		get_table_name(ATT_POLICY)))

	frappe.db.commit()

	_delete_associations = """
		DELETE FROM `{0}`
	""".format(get_table_name(EMP_ATT_ASSOCIATION))

	_add_employee_associations = """
		INSERT INTO `{0}` (`name`, `employee`,`attendance_policy`,`creation`)
   		SELECT `name`, `employee`,`attendance_policy`,NOW() AS creation from `{1}`;
	""".format(
		get_table_name(EMP_ATT_ASSOCIATION), 
		get_table_name(EMP_ATT_ASSOCIATION_BUFF)
		)

	try:
		frappe.db.begin()

		frappe.db.sql(_delete_associations)
		frappe.db.sql(_add_employee_associations)

	except Exception as e:
		frappe.db.rollback()
		frappe.throw(_("Cannot able to insert associations"))

	else:
		frappe.db.commit()

