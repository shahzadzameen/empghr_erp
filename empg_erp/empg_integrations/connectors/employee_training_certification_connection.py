from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeTrainingCertificationConnection(BaseConnection):
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
                ecd.id,
                u.employeeId as parent,
                'training_and_certification_details' as parentfield,
                'Employee' as parenttype,
                ecd.course_name,
                ecd.course_level,
                ecd.course_offered_by,
                ecd.certification_name,
                ecd.description,
                ecd.issued_date
            FROM
                main_empcertificationdetails ecd
                    INNER JOIN
                main_users u ON u.id = ecd.user_id
            WHERE
                ecd.isactive = 1;""")
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