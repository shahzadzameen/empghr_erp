from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeCurrentAddressConnection(BaseConnection):
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
                concat(ecd.id, 'c') as id,
                u.employeeId as parent,
                'address' as parentfield,
                'Employee' as parenttype,
                ecd.current_streetaddress as street_address,
                c.country_name as country,
                s.state_name as state,
                city.city_name as city,
                ecd.current_pincode as postal_code,
                'Current' as `type`
            FROM
                main_empcommunicationdetails ecd
                    INNER JOIN
                main_users u ON u.id = ecd.user_id
                INNER JOIN
                tbl_countries c ON c.id = ecd.current_country
                INNER JOIN
                tbl_cities city ON city.id = ecd.current_city
                INNER JOIN
                tbl_states s ON s.id = ecd.current_state
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