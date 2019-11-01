from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb
from datetime import datetime

class EmployeeShiftConnection(BaseConnection):
	weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	empty_holday_list_name = 'No Off Days'
	holiday_list_start_date_default = '2015-01-01'
	holiday_list_end_date_default = '2022-12-31'
	off_status_id = 2
	
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
			select 
			u.id,
			u.employeeId as employee,
			DATE_FORMAT(es.date_of_joining, '%Y-%m-%d') as from_date,
			DATE_FORMAT(IF(es.date_of_leaving IS NULL OR es.date_of_leaving = '00-00-0000' OR es.date_of_leaving = '', DATE_ADD(DATE_FORMAT(NOW(),'%Y-01-31'), INTERVAL 2 MONTH), es.date_of_leaving), '%Y-%m-%d') as to_date,
			time_format(
				IF(erws.id IS NOT NULL, erws.shift_start, erws_d.shift_start), 
				'%H:%i:%s') AS shift_start,
			time_format(
				IF(
					erws.id IS NOT NULL,
					IF( 
						HOUR(ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60))) > 23,
						SUBTIME(
							ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)),
							SEC_TO_TIME(24*60*60)
						),
						ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)) 
					),
					ADDTIME(erws_d.shift_start, SEC_TO_TIME(erws_d.working_hours*60*60))
				) 
				,'%H:%i:%s') AS shift_end,
			IF(erws.id IS NOT NULL, erws.working_hours, erws_d.working_hours) as working_hours,
			IF(erws.id IS NOT NULL, erws.wd1, erws_d.wd1) as 'Monday',
			IF(erws.id IS NOT NULL, erws.wd2, erws_d.wd2) as 'Tuesday',
			IF(erws.id IS NOT NULL, erws.wd3, erws_d.wd3) as 'Wednesday',
			IF(erws.id IS NOT NULL, erws.wd4, erws_d.wd4) as 'Thursday',
			IF(erws.id IS NOT NULL, erws.wd5, erws_d.wd5) as 'Friday',
			IF(erws.id IS NOT NULL, erws.wd6, erws_d.wd6) as 'Saturday',
			IF(erws.id IS NOT NULL, erws.wd7, erws_d.wd7) as 'Sunday'
			from main_users u 
			left join main_employees_summary es on u.id = es.user_id 
			left join main_employee_roster_weekly_schedule erws on u.id = erws.user_id 
			left join main_employee_roster_weekly_schedule erws_d on 0 = erws_d.user_id
			where (u.employeeId IS NOT NULL OR u.employeeId != '' limit 10)
			""")
		cursor = self.connection.cursor(dictionary=True)

		cursor.execute(query)
		records = []
		for data in cursor:
			data['employee'] = data['employee'].replace('EMPG', '')
			emp = frappe.db.get_value("Employee", data['employee'])
			if emp is None:
				frappe.log(str(emp) + ' not found during shift assignment.')

			shift_type_name = data['shift_start'] + ' - ' + data['shift_end']
			off_days_string = self.get_holiday_list_name(data)
			if off_days_string != '':
				shift_type_name += ' | ' + off_days_string

			shift_assignment_data = {
				"id" : data['id'],
				"shift_type" : shift_type_name,
				"employee" : data['employee'],
				"from_date" : data['from_date'],
				"to_date" : data['to_date'],
				"docstatus" : 1
			}
			_filters = shift_assignment_data.copy()
			del(_filters["id"])
			if frappe.db.get_value("Shift Request", _filters) is None:
				records.append(shift_assignment_data)
		cursor.close()
		
		return list(records)

	def __del__(self):
		self.connection.close()

	def get_shift_type_name(self, roster):
		shift_name = roster['shift_start'] + ' - ' + roster['shift_end']
		off_days_string = self.get_holiday_list_name(roster)
		if off_days_string != '':
			shift_name += ' | ' + off_days_string
		return shift_name
	
	def get_holiday_list_name(self, roster):
		off_days = []
		off_days_string = ''
		for weekday in self.weekdays:
			if roster[weekday] == self.off_status_id:
				off_days.append(weekday[:3])
		joiner = '-'
		off_days_string = joiner.join(off_days)
		if off_days_string == '':
			return self.empty_holday_list_name
		else:
			return off_days_string

	def create_shift_type(self, roster):
		shift_type_name = self.get_shift_type_name(roster)
		holiday_list_name = self.get_holiday_list_name(roster)
		if not frappe.db.exists("Holiday List", holiday_list_name):
			self.create_holiday_list(holiday_list_name, roster)
		shift_type_data = {
			"doctype" : "Shift Type",
			"name" : shift_type_name,
			"start_time" : roster['shift_start'],
			"end_time" : roster['shift_end'],
			"holiday_list" : holiday_list_name
		}
		shift_type =  frappe.get_doc(shift_type_data)
		shift_type.insert()

	def create_holiday_list(self, holiday_list_name, roster):
		doc_data = {
			"doctype" : "Holiday List",
			"holiday_list_name" : holiday_list_name,
			"from_date" : self.holiday_list_start_date_default,
			"to_date" : self.holiday_list_end_date_default
		}
		holiday_list = frappe.get_doc(doc_data)
		holiday_list.insert()

		if holiday_list_name != self.empty_holday_list_name:
			for weekday in self.weekdays:
				if roster[weekday] == self.off_status_id:
					holiday_list.weekly_off = weekday
					holiday_list.get_weekly_off_dates()
		holiday_list.save()


def create_shifts():
	connector =  frappe.get_doc('Data Migration Connector', 'EMPGHR Weekly Roster Connector')
	print(connector.name)
	empShiftCon = EmployeeShiftConnection(connector)

	query = ("""
				select 
				u.id,
				u.employeeId as employee,
				DATE_FORMAT(es.date_of_joining, '%Y-%m-%d') as from_date,
				DATE_FORMAT(IF(es.date_of_leaving IS NULL OR es.date_of_leaving = '00-00-0000' OR es.date_of_leaving = '', DATE_ADD(DATE_FORMAT(NOW(),'%Y-01-31'), INTERVAL 2 MONTH), es.date_of_leaving), '%Y-%m-%d') as to_date,
				time_format(
					IF(erws.id IS NOT NULL, erws.shift_start, erws_d.shift_start), 
					'%H:%i:%s') AS shift_start,
				time_format(
					IF(
						erws.id IS NOT NULL,
						IF( 
							HOUR(ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60))) > 23,
							SUBTIME(
								ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)),
								SEC_TO_TIME(24*60*60)
							),
							ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)) 
						),
						ADDTIME(erws_d.shift_start, SEC_TO_TIME(erws_d.working_hours*60*60))
					) 
					,'%H:%i:%s') AS shift_end,
				IF(erws.id IS NOT NULL, erws.working_hours, erws_d.working_hours) as working_hours,
				IF(erws.id IS NOT NULL, erws.wd1, erws_d.wd1) as 'Monday',
				IF(erws.id IS NOT NULL, erws.wd2, erws_d.wd2) as 'Tuesday',
				IF(erws.id IS NOT NULL, erws.wd3, erws_d.wd3) as 'Wednesday',
				IF(erws.id IS NOT NULL, erws.wd4, erws_d.wd4) as 'Thursday',
				IF(erws.id IS NOT NULL, erws.wd5, erws_d.wd5) as 'Friday',
				IF(erws.id IS NOT NULL, erws.wd6, erws_d.wd6) as 'Saturday',
				IF(erws.id IS NOT NULL, erws.wd7, erws_d.wd7) as 'Sunday'
				from main_users u 
				left join main_employees_summary es on u.id = es.user_id 
				left join main_employee_roster_weekly_schedule erws on u.id = erws.user_id 
				left join main_employee_roster_weekly_schedule erws_d on 0 = erws_d.user_id
				where (u.employeeId IS NOT NULL OR u.employeeId != '')
				""")
	cursor = empShiftCon.connection.cursor(dictionary=True)

	cursor.execute(query)
	records = []
	for data in cursor:
		try:
			data['employee'] = data['employee'].replace('EMPG', '')
			shift_type_name = empShiftCon.get_shift_type_name(data)
			print(shift_type_name)
			if not frappe.db.exists("Shift Type", shift_type_name):
				empShiftCon.create_shift_type(data)
			emp = frappe.db.get_value("Employee", data['employee'])
			if emp is not None:
				emp_doc = frappe.get_doc("Employee", data['employee'])
				emp_doc.shift_type = shift_type_name
				emp_doc.save()
		except Exception as err:
			print(str(err))
			frappe.log(str(err))
			pass
	cursor.close()

	return list(records)


def create_shift_requests():
	connector = frappe.get_doc('Data Migration Connector', 'EMPGHR Weekly Roster Connector')
	print(connector.name)
	empShiftCon = EmployeeShiftConnection(connector)

	query = ("""
				select 
				u.id,
				u.employeeId as employee,
				DATE_FORMAT(es.date_of_joining, '%Y-%m-%d') as from_date,
				DATE_FORMAT(IF(es.date_of_leaving IS NULL OR es.date_of_leaving = '00-00-0000' OR es.date_of_leaving = '', DATE_ADD(DATE_FORMAT(NOW(),'%Y-01-31'), INTERVAL 2 MONTH), es.date_of_leaving), '%Y-%m-%d') as to_date,
				time_format(
					IF(erws.id IS NOT NULL, erws.shift_start, erws_d.shift_start), 
					'%H:%i:%s') AS shift_start,
				time_format(
					IF(
						erws.id IS NOT NULL,
						IF( 
							HOUR(ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60))) > 23,
							SUBTIME(
								ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)),
								SEC_TO_TIME(24*60*60)
							),
							ADDTIME(erws.shift_start, SEC_TO_TIME(erws.working_hours*60*60)) 
						),
						ADDTIME(erws_d.shift_start, SEC_TO_TIME(erws_d.working_hours*60*60))
					) 
					,'%H:%i:%s') AS shift_end,
				IF(erws.id IS NOT NULL, erws.working_hours, erws_d.working_hours) as working_hours,
				IF(erws.id IS NOT NULL, erws.wd1, erws_d.wd1) as 'Monday',
				IF(erws.id IS NOT NULL, erws.wd2, erws_d.wd2) as 'Tuesday',
				IF(erws.id IS NOT NULL, erws.wd3, erws_d.wd3) as 'Wednesday',
				IF(erws.id IS NOT NULL, erws.wd4, erws_d.wd4) as 'Thursday',
				IF(erws.id IS NOT NULL, erws.wd5, erws_d.wd5) as 'Friday',
				IF(erws.id IS NOT NULL, erws.wd6, erws_d.wd6) as 'Saturday',
				IF(erws.id IS NOT NULL, erws.wd7, erws_d.wd7) as 'Sunday'
				from main_users u 
				left join main_employees_summary es on u.id = es.user_id 
				left join main_employee_roster_weekly_schedule erws on u.id = erws.user_id 
				left join main_employee_roster_weekly_schedule erws_d on 0 = erws_d.user_id
				where (u.employeeId IS NOT NULL OR u.employeeId != '') 
				""")
	cursor = empShiftCon.connection.cursor(dictionary=True)

	cursor.execute(query)
	records = []
	for data in cursor:
		try:
			data['employee'] = data['employee'].replace('EMPG', '')
			emp = frappe.db.get_value("Employee", data['employee'])
			if emp is None:
				print('Employee with ID ' + str(data['employee']) + ' not found during shift assignment.')
				frappe.log(str(data['employee']) + ' not found during shift assignment.')

			shift_type_name = data['shift_start'] + ' - ' + data['shift_end']
			off_days_string = empShiftCon.get_holiday_list_name(data)
			if off_days_string != '':
				shift_type_name += ' | ' + off_days_string

			shift_assignment_data = {
				"doctype": "Shift Request",
				"shift_type": shift_type_name,
				"employee": data['employee'],
				"from_date": data['from_date'],
				"to_date": data['to_date'],
				"docstatus": 1
			}

			_filters = shift_assignment_data.copy()
			del (_filters["doctype"])
			if frappe.db.get_value("Shift Request", _filters) is None:
				doc = frappe.get_doc(shift_assignment_data)
				doc.save()
		except Exception as err:
			print(str(err))
			frappe.log(str(err))
			pass
	cursor.close()

	return list(records)