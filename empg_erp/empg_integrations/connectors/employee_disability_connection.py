from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeDisabilityConnection(BaseConnection):
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

		query = ("""
			SELECT 
                edd.id,
                u.employeeId as parent,
                'disability_details' as parentfield,
                'Employee' as parenttype,
                edd.disability_name as disability,
                edd.disability_description as reason,
                edd.disability_type as disability_type
            FROM
                main_empdisabilitydetails edd
                    INNER JOIN
                main_users u ON u.id = edd.user_id
            WHERE
                edd.isactive = 1""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		records = []
		for data in cursor:
			data['parent'] = data['parent'].replace('EMPG', '')
			records.append(data)
		cursor.close()
		return list(records)

	def __del__(self):
		self.connection.close()