from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeeLeaveRequestConnection(BaseConnection):
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

		status_mappings = {
			"Pending for approval" : "Open",
			"Approved" : "Approved",
			"Rejected" : "Rejected",
			"Cancel" : "Cancelled"
		}

		query = ("""
			SELECT 
				lrs.id as id,
				u.employeeId as employee,
				lrs.leavetype_name as leave_type,
				DATE_FORMAT(lrs.from_date, '%Y-%m-%d') as from_date,
				DATE_FORMAT(lrs.to_date, '%Y-%m-%d') as to_date,
				lrs.appliedleavescount as total_leave_days,
				lrs.reason as description,
				
				if(lrs.leaveday = 2, 1, NULL) as half_day,
				if(lrs.leaveday = 2, lrs.to_date, NULL) as half_day_date,
				
				if(lrs.leaveday = 3, 1, NULL) as hourly,
				if(lrs.leaveday = 3, format(round(lrs.appliedleavescount*9), 0), NULL) as hours,
				if(lrs.leaveday = 3, lrs.to_date, NULL) as hourly_day_date,
				
				IF(mngr.emailaddress IS NULL, 'Administrator', mngr.emailaddress) as leave_approver,
				lrs.leavestatus as `status`,
				DATE_FORMAT(lrs.createddate, '%Y-%m-%d') as posting_date,
				lrs.approver_comments as comments,
				0 as follow_via_email
			FROM
				main_leaverequest_summary lrs
			INNER JOIN
				main_users u ON u.id = lrs.user_id
			LEFT JOIN
				main_users mngr ON mngr.id = lrs.rep_mang_id
			WHERE
				u.employeeId IS NOT NULL AND lrs.isactive = 1""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		records = []
		for data in cursor:
			data['employee'] = data['employee'].replace('EMPG', '')
			data['leave_type'] = leave_mappings[data['leave_type']]
			data['status'] = status_mappings[data['status']]
			data['docstatus'] = 1 if data['status'] in ['Approved', 'Rejected'] else 0
			print(data['description'])
			if data['description'] != 'Penalty Deduction':
				continue
			records.append(data)
		cursor.close()
		
		return list(records)

	def __del__(self):
		self.connection.close()