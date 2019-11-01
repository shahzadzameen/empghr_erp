from datetime import datetime, timedelta
import frappe
from dateutil.relativedelta import relativedelta
import calendar
from empg_erp.utils import get_config_by_name
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE, ROSTER_STATUS_FLEXIBLE, \
    ROSTER_STATUS_ON, ROSTER_STATUS_HOLIDAY, ROSTER_STATUS_OFF

from frappe.utils.background_jobs import enqueue

class EmployeeRoster():

    def __init__(self, interval = 2, employee = None):

        self.interval = interval
        self.employee = employee
        self.employee_shift = []
        self.employee_attendance = []
        self.dates = []

        _start_date = datetime.today().replace(day=1)
        _current_month = int(datetime.strftime(_start_date, "%m"))
        _current_year = int(datetime.strftime(_start_date, "%Y"))
        _end_date = """{0}-{1}-{2}""".format(
            _current_year,
            _current_month,
            calendar.monthrange(_current_year, _current_month)[1]
        )

        self.start_date = (datetime.today().replace(day=1) - relativedelta(months=(interval-1)))
        self.end_date = datetime.strptime(_end_date, "%Y-%m-%d")
       
    def prepare_employee_data(self):

        _df_start_time = get_config_by_name("default_shift_start_time", "09:00:00")
        _df_end_time = get_config_by_name("default_shift_end_time", "18:00:00")
        _employee_cond = ""

        if self.employee:
            _employee_cond = """ AND e.name = "{0}" """.format(self.employee)

        self.employee_attendance = frappe.db.sql("""
            SELECT
            e.name,  
            IF(st.start_time IS NULL,%(start_time)s,st.start_time) as start_time,
            IF(st.end_time IS NULL,%(end_time)s,st.end_time) as end_time,
            e.company, mc.week_day_date as week_day,
            e.department,
            IF(h.name IS NULL AND ch.name IS NULL AND erch.name IS NULL, 
                IF(week_day_date = e.date_of_joining, "{1}", "{2}"), 
                IF(ch.name IS NOT NULL, "{3}", "{4}")
                ) as attendance_status,            
            IF(h.name IS NULL AND ch.name IS NULL AND erch.name IS NULL, "Absent", "Present") as status
            FROM `month_calendar` mc 
            INNER JOIN `tabEmployee` e ON mc.emp_fk = "employee" AND e.status = "Active" {0}
            LEFT JOIN `tabAttendance` att ON att.employee = e.name 
            AND att.attendance_date = mc.week_day_date
            LEFT JOIN `tabEmployee` es
            ON es.name = e.name
            INNER JOIN `tabShift Type` st
            ON st.name = es.shift_type
            LEFT JOIN
            `tabHoliday List` hl ON hl.name = e.holiday_list
            LEFT JOIN
            `tabHoliday` h ON h.parent = hl.name AND h.holiday_date = mc.week_day_date
            LEFT JOIN
            `tabCompany` c ON c.name = e.company
            LEFT JOIN
            `tabHoliday List` chl ON chl.name = c.default_holiday_list
            LEFT JOIN
            `tabHoliday` ch ON ch.parent = chl.name AND ch.holiday_date = mc.week_day_date
            LEFT JOIN
            `tabHoliday List` erhl ON erhl.name = st.holiday_list
            LEFT JOIN
            `tabHoliday` erch ON erch.parent = erhl.name AND erch.holiday_date = mc.week_day_date

            WHERE att.name IS NULL
            AND mc.week_day_date >= e.date_of_joining
            GROUP BY e.name, mc.week_day_date
        """.format(_employee_cond, ROSTER_STATUS_FLEXIBLE, ROSTER_STATUS_ON, ROSTER_STATUS_HOLIDAY, ROSTER_STATUS_OFF),
        {
            "start_time" : _df_start_time,
            "end_time" : _df_end_time
        }, as_dict = True)

    def generate_shift(self):

        for emp_shift in self.employee_shift:
            enqueue("empg_erp.modules.mustang.employee.employee_roster.save_shift", emp_shift = emp_shift)

    def generate_attendance(self):

        for emp_att in self.employee_attendance:
            enqueue("empg_erp.modules.mustang.employee.employee_roster.save_attendance", emp_att = emp_att)

    def create_monthly_calendar(self):

        delta = self.end_date - self.start_date
        dates = []

        for i in range(delta.days + 2):
            current_date = self.start_date + timedelta(days=i)
            dates.append(datetime.strftime(current_date, "%Y-%m-%d"))

        frappe.db.commit()

        frappe.db.sql("""
            DROP TEMPORARY TABLE IF EXISTS month_calendar;
        """)
        frappe.db.sql("""
            CREATE TEMPORARY TABLE IF NOT EXISTS month_calendar (week_day_date DATE, emp_fk varchar(8) default "employee");
        """)
        frappe.db.sql("""
            INSERT INTO month_calendar (`week_day_date`)
            VALUES {0};
        """.format("('" + "'),('".join(dates) + "')"))

        frappe.db.commit()

    def run(self):

        try:
            self.create_monthly_calendar()
            self.prepare_employee_data()

            self.generate_attendance()

            return "success"
        except Exception as err:
            return err

    def get_employee_roster():

        return self.employee_attendance

    @classmethod
    def is_cutoff_passed(cls, date, months_back = None):
        '''
        will check if cutoff date is passed, starting from 21st of last month
        '''
        date = datetime.strptime(str(date), "%Y-%m-%d")
        today = datetime.today()
        if months_back:
            today = today - relativedelta(months=months_back)

        if int(today.day) <= MONTHLY_ATTENDANCE_DATE:
            today = today - relativedelta(months=1)

        cutoff_date = datetime(today.year, today.month, MONTHLY_ATTENDANCE_DATE)

        if date > cutoff_date:
            return False
        else:
            return True

def save_attendance(emp_att):

    emp_attendance = frappe.get_doc({
        "doctype" : "Attendance",
        "employee" : emp_att["name"],
        "status" : emp_att["status"],
        "attendance_status" : emp_att["attendance_status"],
        "shift_start_time" : emp_att["start_time"],
        "shift_end_time" : emp_att["end_time"],
        "attendance_date" : emp_att["week_day"],
        "company" : emp_att["company"],
        "department" : emp_att["department"],
        "docstatus" : 1
    })

    try:
        emp_attendance.set_by_cron = 1
        emp_attendance.save()
    except Exception as err:
        frappe.log_error(err)

