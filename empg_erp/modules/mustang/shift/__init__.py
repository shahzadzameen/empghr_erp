import frappe
from .employee_shift import EmployeeShift
from empg_erp.utils import get_config_by_name
import datetime
from empg_erp.utils import get_time_diff, get_employee_shift_timings

def get_employee_shift(emp_id, att_date):

    shift_list = []

    if emp_id:
        shift_list = frappe.db.sql("""
            SELECT TIME_FORMAT(shift_start_time, %(date_format)s) as start_time,
            TIME_FORMAT(shift_end_time, %(date_format)s) as end_time, attendance_date as date
            FROM `tabAttendance`
            WHERE employee=%(employee)s AND attendance_date=%(date)s AND docstatus = 1
            """,{"date_format" : "%H:%i:%s","employee":emp_id, "date":att_date}, as_dict = True)

    if len(shift_list) == 0:

        _emp_shift = get_employee_shift_timings(emp_id)
        _shift = dict({
            "start_time" : _emp_shift.start_time,
            "end_time" : _emp_shift.end_time,
            "date" : att_date
        })
        shift_list.append(_shift)

    return EmployeeShift(shift_list)

def get_employee_shift_working_hours(emp_id):
    working_hours = []
    if emp_id:
        working_hours = frappe.db.sql("""
            SELECT
               FLOOR(emp.working_hours / total) AS working_hours
            FROM
               (SELECT
                   COUNT(0) AS total,
                       SUM(TIME_FORMAT(TIMEDIFF(st.shift_end_time, st.shift_start_time), '%h')) AS working_hours
               FROM
                   `tabAttendance` AS st
               WHERE
                   st.attendance_date >= DATE_FORMAT(NOW(), '%Y-01-01')
                       AND employee = '{0}'
               GROUP BY employee) AS emp
            """.format(emp_id), as_dict = True)

    if len(working_hours) == 0:
        default_time = dict({
            "start_time" : get_config_by_name("default_shift_start_time", "09:00:00"),
            "end_time" : get_config_by_name("default_shift_end_time", "18:00:00"),
            "date": datetime.datetime.today().strftime('%Y-%m-%d')
        })
        working_hours = calculate_working_hours_for_default(default_time)
    else:
        working_hours = working_hours[0]['working_hours']
    return working_hours


def calculate_working_hours_for_default(default_time):
    today_shift_start = "{0} {1}".format(default_time['date'], default_time['start_time'])
    today_shift_end = "{0} {1}".format(default_time['date'], default_time['end_time'])
    working_hours = get_time_diff(today_shift_end, today_shift_start, 'hours')
    return working_hours

def get_holiday_list_from_employee_shift(employee):
    response = None
    result =  frappe.db.sql("""
    SELECT 
        sh_type.holiday_list as holiday
    FROM
        `tabShift Type` sh_type
    LEFT JOIN `tabEmployee` emp
        ON `sh_type`.`name` = emp.shift_type
    WHERE 
        emp.employee=%(employee)s
    """,({"employee":employee}),as_dict = True)
    if(result and len(result)):
        response = result[0].holiday
    return response