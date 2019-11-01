from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class UserConnection(BaseConnection):
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
				u.id AS id,
				u.firstname AS firstname,
				u.lastname AS lastname,
				u.emailaddress AS email,
				IF(g.gendername IS NOT NULL, g.gendername, 'Other') AS gender,
				'Asia/Karachi' as time_zone,
				0 as send_welcome_email,
                IF(es.date_of_joining < epd.dob OR epd.dob IS NULL OR epd.dob = '', '1000-01-01', epd.dob) AS dob
			FROM
				main_users u
				INNER JOIN
				main_employees_summary es ON u.id = es.user_id
				INNER JOIN
				main_employees e ON u.id = e.user_id
				LEFT JOIN
				main_emppersonaldetails epd ON u.id = epd.user_id
				LEFT JOIN
				main_gender g ON epd.genderid = g.id
				INNER JOIN
				main_locations ol ON e.location_id = ol.id
				INNER JOIN
				main_locations oc ON oc.id = ol.parent_id
				INNER JOIN
				main_locations osr ON osr.id = oc.parent_id
				INNER JOIN
				main_locations orgn ON orgn.id = osr.parent_id
				LEFT JOIN
				main_empsegmentations d ON d.user_id = u.id AND d.segment_id = 1
				LEFT JOIN
				main_segment_options dso ON dso.id = d.segment_option_id
				LEFT JOIN
				main_empsegmentations c ON c.user_id = u.id AND c.segment_id = 2
				LEFT JOIN
				main_segment_options cso ON cso.id = c.segment_option_id
				LEFT JOIN
				main_empsegmentations dc ON dc.user_id = u.id AND dc.segment_id = 3
				LEFT JOIN
				main_segment_options dcso ON dcso.id = dc.segment_option_id
				LEFT JOIN
				main_empsegmentations stdd ON stdd.user_id = u.id AND stdd.segment_id = 4
				LEFT JOIN
				main_segment_options stddso ON stddso.id = stdd.segment_option_id
				LEFT JOIN
				main_maritalstatus msts ON msts.id = epd.maritalstatusid
				LEFT JOIN
				main_religions rlg ON rlg.id = epd.religionid
				LEFT JOIN
				main_nationality nlty ON nlty.id = epd.nationalityid
			WHERE
				es.employeeId IS NOT NULL and es.emailaddress IS NOT NULL""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		employee = []
		for data in cursor:
			employee.append(data)
		
		cursor.close()

		return list(employee)

	def __del__(self):
		self.connection.close()