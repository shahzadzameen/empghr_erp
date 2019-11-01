from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeePersonalContactConnection(BaseConnection):
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
			frappe.throw(("Error: {}".format(error)))

		self.name_field = 'id'

	def insert(self, doctype, doc):
		pass

	def update(self, doctype, doc, migration_id):
		pass

	def delete(self, doctype, migration_id):
		pass

	def get(self, remote_objectname, fields=None, filters=None, start=0, page_length=10):

		query = ("""
			SELECT 
				concat(ecd.id, 'p') as id,
				u.employeeId as parent,
				'employee_contact_details' as parentfield,
				'Employee' as parenttype,
				ecd.personalemail AS email,
				'Personal' AS `type`
			FROM
				main_users u
					INNER JOIN
				main_employees_summary es ON u.id = es.user_id
					LEFT JOIN
				main_empcommunicationdetails ecd ON u.id = ecd.user_id
			WHERE
			ecd.personalemail IS NOT NULL
				AND es.employeeId IS NOT NULL;""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		employee = []
		for data in cursor:
			data['parent'] = data['parent'].replace('EMPG', '')
			employee.append(data)
		
		cursor.close()
		return list(employee)

	def __del__(self):
		self.connection.close()