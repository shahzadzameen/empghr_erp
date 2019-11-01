from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeLeavesConnection(BaseConnection):
	def __init__(self, connector):
		self.connector = connector

		try:
			password = self.get_password()
		except frappe.AuthenticationError:
			password = None

		try:
			self.connection = mariadb.connect(
				host=self.connector.hostname,
				user=self.connector.username, 
				password=password,
				database=self.connector.database_name 
				)

		except mariadb.Error as error:
			print("Error: {}".format(error))
			frappe.throw(("Error: {}".format(error)))

		self.name_field = 'id'

	def insert(self, doctype, doc):
		pass

	def update(self, doctype, doc, migration_id):
		pass

	def delete(self, doctype, migration_id):
		pass

	def get(self, remote_objectname, fields=None, filters=None, start=0, page_length=10):
		leave_mappings = {
			"Casual" : "Casual Leave",
			"Sick" : "Sick Leave",
			"Annual" : "Annual Leave"
		}
		query = ("""
			select 
			empl.id,
			u.employeeId as employee,
			empl.emp_leave_limit as new_leaves_allocated,
			IF(es.date_of_joining > concat(empl.alloted_year,'-01-01'), es.date_of_joining, concat(empl.alloted_year,'-01-01')) as from_date,
			concat(empl.alloted_year,'-12-31') as to_date,
			emplt.leavetype as leave_type,
			1 as docstatus
			from main_users u 
			inner join main_employees_summary es on u.id = es.user_id
			inner join main_employeeleaves empl on u.id = empl.user_id
			inner join main_employeeleavetypes emplt on empl.leave_type = emplt.id
			where u.employeeId is not null;""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		records = []
		for data in cursor:
			data['employee'] = data['employee'].replace('EMPG', '')
			data['leave_type'] = leave_mappings[data['leave_type']]
			records.append(data)
		cursor.close()
		return list(records)

	def __del__(self):
		self.connection.close()