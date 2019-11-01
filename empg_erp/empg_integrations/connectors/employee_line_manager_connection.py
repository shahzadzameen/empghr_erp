from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeLineManagerConnection(BaseConnection):
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
		# make the pull id same as emp migration pull id
		mng_mapping_name = 'ZN Employee Line Manager to ERPNext Line Manager'
		emp_migration_pull_id = 'empghr_employees_pull_id'
		mng_mapping = frappe.get_doc('Data Migration Mapping', mng_mapping_name)
		mng_mapping.migration_id_field = emp_migration_pull_id
		mng_mapping.save()

		query = ("""
			SELECT 
				u.id AS id,
				mngr.employeeId as reports_to,
				IF(g.gendername = 'MALE', 'Mr', IF(g.gendername = 'FEMALE', 'Miss', '')) AS salutation,
				u.firstname AS firstname,
				u.lastname AS lastname,
				u.fathername AS father_name,
				u.emailaddress AS email,
				es.employeeId AS employee_number,
				IF(u.isactive = 1, es.emp_status_name, 'Left') AS employment_type,
				es.date_of_joining AS doj,
				IF(es.date_of_joining < epd.dob OR epd.dob IS NULL OR epd.dob = '', '1000-01-01', epd.dob) AS dob,
				e.date_of_probation_completion as date_of_probation_completion,
				IF(g.gendername IS NOT NULL, g.gendername, 'Other') AS gender,
				IF(epd.cnic IS NOT NULL OR epd.cnic != '', epd.cnic, '00000-0000000-0') as cnic,
				cso.segment_option as company,
				es.years_exp as years_of_experience,
				'Asia/Karachi' as time_zone,
				0 as send_welcome_email,
				IF(ol.location IS NOT NULL, ol.location, 'No Office Location') as office_location,
				IF(oc.location IS NOT NULL, oc.location, 'No Office City') as office_city,
				IF(osr.location IS NOT NULL, osr.location, 'No Office Sub Region') as office_sub_region,
				IF(orgn.location IS NOT NULL, orgn.location, 'No Office Region') as office_region,
				es.businessunit_name as department ,
				es.department_name as sub_department ,
				es.jobtitle_name as job_title,
				IF(dso.segment_option IS NOT NULL, dso.segment_option, 'No Division') as division,
				dcso.segment_option as designation_category,
				stddso.segment_option as standardized_designation,
				upper(epd.bloodgroup) as blood_group,
				msts.maritalstatusname as marital_status,
				rlg.religionname as religion,
				nlty.nationalitycode as nationality
			FROM
				main_users u
				INNER JOIN
				main_employees_summary es ON u.id = es.user_id
				INNER JOIN
				main_employees e ON u.id = e.user_id
				INNER JOIN
				main_employees_summary mngr ON es.reporting_manager = mngr.user_id
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
				es.employeeId IS NOT NULL""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		employee = []
		for data in cursor:
			data['employee_number'] = data['employee_number'].replace('EMPG', '')
			data['reports_to'] = data['reports_to'].replace('EMPG', '')

			user_id = frappe.db.get_value("Employee", data['reports_to'], ["user_id"])
			if user_id is not None:
				user = frappe.get_doc("User", user_id)
				user.add_roles("Line Manager", "Leave Approver")

			employee.append(data)
		
		cursor.close()

		return list(employee)

	def __del__(self):
		self.connection.close()