from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeAttendanceConnection(BaseConnection):
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
                erd.id AS id,
                es.employeeId AS employee,
                erd.date AS attendance_date,
                eatt.checkin_time AS check_in,
                eatt.checkout_time AS check_out,
                eatt.late_arrival AS late_arrival,
                eatt.early_left AS left_early,
                eatt.working_hours AS working_hours,
                rs.title as attendance_status,
                CASE
                    WHEN eatt.id IS NOT NULL THEN 'Present'
                    WHEN eatt.id IS NULL AND lr.id IS NULL AND !rs.consider_absent THEN 'Present'
                    WHEN eatt.id IS NULL AND lr.id IS NULL AND rs.consider_absent THEN 'Absent'
                    WHEN eatt.id IS NULL AND lr.id IS NOT NULL AND lr.appliedleavescount >= 1 THEN 'On Leave'
                    WHEN eatt.id IS NULL AND lr.id IS NOT NULL AND lr.appliedleavescount = 0.5 THEN 'Halfday'
                    WHEN eatt.id IS NULL AND lr.id IS NOT NULL AND lr.appliedleavescount < 0.5 THEN 'Hourly'
                END AS `status`,
                concat(lt.leavetype, ' Leave') AS `leave_type`,
                cso.segment_option as company,
                1 as docstatus,
                time_format( erd.shift_start, '%H:%i:%s') AS shift_start_time,
				time_format(
					ADDTIME(erd.shift_start, SEC_TO_TIME(erd.working_hours*60*60)) 
					,'%H:%i:%s') 
				AS shift_end_time
            FROM
                main_employee_roster_daily erd
            LEFT JOIN
                main_empattendance eatt ON eatt.user_id = erd.user_id
                    AND eatt.attendance_date = erd.date
            LEFT JOIN
                main_employees_summary es ON es.user_id = erd.user_id
            LEFT JOIN
                main_leaverequest lr ON lr.user_id = erd.user_id
                    AND lr.leavestatus = 'Approved'
                    AND (erd.date BETWEEN lr.from_date AND lr.to_date)
            LEFT JOIN
                main_employeeleavetypes lt ON lt.id = lr.leavetypeid
            LEFT JOIN
                main_roster_statuses rs ON rs.id = erd.status_id
			LEFT JOIN
				main_empsegmentations c ON c.user_id = erd.user_id AND c.segment_id = 2
			LEFT JOIN
				main_segment_options cso ON cso.id = c.segment_option_id
            WHERE
                es.employeeId IS NOT NULL""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		employee = []
		for data in cursor:
			data['employee'] = data['employee'].replace('EMPG', '')
			employee.append(data)
		
		cursor.close()

		return list(employee)

	def __del__(self):
		self.connection.close()