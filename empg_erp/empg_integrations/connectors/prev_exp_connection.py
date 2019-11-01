from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class PrevExpConnection(BaseConnection):
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
				ed.id,
				u.employeeId as parent,
				'external_work_history' as parentfield,
				'Employee' as parenttype,
				ed.comp_name as company_name,
				ed.comp_website as company_website,
				ed.designation as designation,
				date_format(ed.from_date, '%Y-%m-%d') as from_date,
				date_format(ed.to_date, '%Y-%m-%d') as to_date,
				ed.reason_for_leaving as reason_for_leaving,
				ed.reference_name as referrer_name,
				ed.reference_contact as referrer_contact,
				ed.reference_email as referrer_email
			FROM
				main_empexperiancedetails ed
					INNER JOIN
				main_users u ON u.id = ed.user_id
			WHERE
				u.employeeId IS NOT NULL AND u.emailaddress IS NOT NULL AND ed.isactive = 1;""")
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