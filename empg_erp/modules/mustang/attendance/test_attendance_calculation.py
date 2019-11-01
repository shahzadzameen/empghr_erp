from __future__ import unicode_literals

import frappe, json, unittest, erpnext

import datetime as dt,datetime
#from empg_erp.modules.zn.attendance import attendance_api
from empg_erp.modules.mustang.attendance import attendance_api

class TestAttendanceCalculation(unittest.TestCase):
    def test_duplicate_attendance(self):

        attendance_date = '2019-08-01'
        checkin = attendance_date + ' ' + '09:00:00'

        employee = make_employee("test_employee_attendance@company1.com")
        removeAttendance(employee)
        removeZKTeco()

        att_data = [{"user_id": employee, "check_time": checkin, "id":1}]
       
        attendance_api(att_data)
        conflict_response = attendance_api(att_data)

        self.assertEquals(409, conflict_response[0]['code'])

    def test_attendance_without_employee(self):
        attendance_date = '2019-08-01'
        checkin = attendance_date + ' ' + '09:00:00'
        att_data = [{"user_id": "90909999", "check_time": checkin, "id":1}]

        att_response = attendance_api(att_data)
        self.assertEquals(400, att_response[0]['code'])

def removeZKTeco():
    frappe.db.sql("delete from `tabZkteko Log`")

def removeAttendance(employee):
    frappe.db.sql("delete from tabAttendance where employee = '%s' " %employee)


def make_employee(user):

    department_name = frappe.get_all("Department", fields="name")[0].name
    
    sub_department_name = frappe.get_all("Department", fields="name",filters = [{"parent_department":department_name}])[0].name

    if not frappe.db.get_value("User", user):
		frappe.get_doc({
			"doctype": "User",
			"email": user,
			"first_name": user,
			"new_password": "password",
			"roles": [{"doctype": "Has Role", "role": "Employee"}]
		}).insert()
 

    if not frappe.db.get_value("Employee", {"user_id": user}):
		employee = frappe.get_doc({
			"doctype": "Employee",
			"naming_series": "EMP-",
			"first_name": user,
			"company": erpnext.get_default_company(),
			"user_id": user,
			"date_of_birth": "1990-05-08",
			"date_of_joining": "2013-01-01",
			"department": department_name,
			"sub_department": sub_department_name,
			"gender": "Female",
			"company_email": user,
			"prefered_contact_email": "Company Email",
			"prefered_email": user,
			"status": "Active",
			"employment_type": "Intern"
		}).insert()
		return employee.name
    else:
		return frappe.get_value("Employee", {"employee_name":user}, "name")