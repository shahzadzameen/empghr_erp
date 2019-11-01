import frappe
import random
import string
from frappe.utils.background_jobs import enqueue

def get_id(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# def create_users(limit=10, default_reports_to='4312', doj='2019-04-01', department='Faker Dpt', sub_department='Faker Sub Dpt'):
#     if frappe.db.get_value('Department', department) is None:
#         _dpt_doc = {
#             'doctype': 'Department',
#             'department_name': department
#         }
#         dpt_doc = frappe.get_doc(_dpt_doc)
#         dpt_doc.insert()
#
#     if frappe.db.get_value('Department', sub_department) is None:
#         _sub_dpt_doc = {
#             'doctype': 'Department',
#             'department_name': sub_department,
#             'parent_department': department
#         }
#         sub_dpt_doc = frappe.get_doc(_sub_dpt_doc)
#         sub_dpt_doc.insert()
#
#     shift_type = "09:00:00 - 18:00:00 | Sat-Sun"
#     default_reports_to = default_reports_to
#
#     iterator = int(limit)
#     employee_numbers = []
#     counter = 1
#
#     while counter <= iterator:
#         user_email = get_id()+'@malinator.com'
#         employee_number = str(random.randint(0, 99999))
#         employee_numbers.append(employee_number)
#
#         if counter > 1 and counter % 6 != 0:
#             lm_index = counter - (counter % 6) - 1
#             lm_index = 0 if lm_index < 0 else lm_index
#             reports_to = employee_numbers[lm_index]
#         else:
#             reports_to = default_reports_to
#         enqueue('empg_erp.modules.mustang.faker.employee.create_new_employee', user_email=user_email, doj=doj, employee_number=employee_number, reports_to=reports_to, shift_type=shift_type)
#         # create_new_employee(user_email, doj, employee_number, reports_to, shift_type)
#         counter = counter + 1


def create_new_employee(user_email, doj, employee_number, reports_to, shift_type):
    _user_doc = {
        'doctype': 'User',
        'email': user_email,
        'first_name': 'Charles',
        'send_welcome_email': 0
    }

    user_doc = frappe.get_doc(_user_doc)
    user_doc.insert()

    _employee_doc = {
        'doctype': 'Employee',
        'first_name': 'Charles '+employee_number,
        'last_name': 'Jackson',
        'employee_number': employee_number,
        'employment_type': 'Full-time',
        'gender': 'Other',
        'cnic': '00000-0000000-0',
        'date_of_birth': '1790-01-04',
        'date_of_joining': doj,
        'department': 'Faker Dpt',
        'sub_department': 'Faker Sub Dpt',
        'reports_to': reports_to,
        'division': 'General',
        'office_region': 'HO',
        'office_sub_region': 'HO',
        'office_city': 'Lahore',
        'office_location': 'Zameen - MM Lahore',
        'shift_type': shift_type,
        'user_id': user_email
    }
    employee_doc = frappe.get_doc(_employee_doc)
    employee_doc.insert()
