from __future__ import unicode_literals
import frappe
from frappe import _
from empg_erp.modules.mustang.shift import get_employee_shift, get_employee_shift_working_hours
from empg_erp.utils import get_employee_code, getPenaltyDateRange
import datetime
from dateutil.relativedelta import relativedelta
import json, ast
from erpnext.hr.utils import to_snake_case
import math
import empg_erp.constants.globals  as _globals
from empg_erp.modules.mustang.employee_penalty.attendance_policies import AttendancePolicies


class TemplateFunctions():

    def __init__(self, *args, **kwargs):
        
        self.template = to_snake_case(kwargs["template"]) if kwargs["template"] else "generic"
        self.widget_data_rows = list()
        self.widget_type = "leftSide"
        self.heading = kwargs["heading"]
        self.redirect_url = kwargs["redirect_url"]
        self.background_color = kwargs["background_color"]
        self.widget_data = kwargs["widget_data"] if len(kwargs["widget_data"]) > 0 else []

    def eval_function(self):

        if hasattr(self, self.template):
            getattr(self, self.template)()
        else:
            self.generic()

    def generic(self):
        self.widget_data_rows =  self.widget_data

    def leave_inner_box_bookmark(self):
        self.generic()
        total = 0
        self.template = "column_inner_box_bookmark"

        for data in self.widget_data:
            total += data.value

        self.widget_data = [{"total" : total}] + self.widget_data

    def emp_monthly_turnover_data(self):
        
        self.generic()
        self.template = "emp_turnover_barchart"

        employee_name = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, 'employee_name')

        turnover_data = []

        for _data in self.widget_data_rows:
            turnover_data.append(_data['turnover'])

        data = [
            {
                "name": employee_name,
                "data": turnover_data
            }
        ]
        
        self.widget_data = ast.literal_eval(json.dumps(data))

    def team_holiday_and_leave(self):

        self.generic()
        self.template = "emp_monthly_turnover_data"

        data = []
        for _data in self.widget_data_rows:
            _tmp_dict = {}
            _tmp_dict["name"] = _data["leave_type"]
            _tmp_dict["data"] = map(int, _data["leave_counts"].split(','))
            data.append((_tmp_dict))
        self.widget_data = ast.literal_eval(json.dumps(data))

    def reward_inner_box_bookmark(self):
        
        self.template = "column_inner_box_bookmark"

        working_hours = get_employee_shift_working_hours(get_employee_code())  # Calculate working hours
        reward_conversion = convert_reward(self.widget_data[0]['reward'], int(working_hours))  # Convert Reward

        for key in reward_conversion:
            self.widget_data_rows.append({"title" : key, "value" : reward_conversion[key]})

        self.widget_data = [{"total" : datetime.datetime.now().year}]

    def penalty_inner_box_bookmark(self):

        self.template = "column_inner_box_bookmark"
        
        result = render_penalty_widget_data()
        self.widget_data = result

    def my_holiday_calendar_bookmark(self):
        self.generic()

        self.widget_type = "rightSide"

    def birthday_bookmark(self):
        self.generic()
        self.widget_type = "rightSide"

    def daily_shift_bookmark(self):
        self.generic()

        daily_dict = []
        for data in self.widget_data_rows:
            description_popover = "Day Status: " + str(data.attendance_status) + \
                                "\nShift Start: " + str(data.shift_start_time) + \
                                "\nShift End: " + str(data.shift_end_time)
            title = str(data.attendance_status)
            description = description_popover
            color = '#45C35E'
            if data.color:
                color = data.color
            date = str(data.attendance_date)
            daily_dict.append({'description': description, 'color': color, 'start': date})

        self.widget_data = ast.literal_eval(json.dumps(daily_dict))

    def announcements_bookmark(self):
        self.generic()
        self.widget_type = "rightSide"

    def column_inner_box_bookmark(self):
        self.generic()

    def profile_score(self):
        if len(self.widget_data) == 0:
            if _globals.ADMINISTRATOR in frappe.get_roles():
                self.widget_data.append({'profile_score': 0, 'employee_name': '#List/Employee/List'})
            else:
                self.widget_data.append({'profile_score': 0, 'employee_name': '#Form/Employee/{0}'.format(get_employee_code())})
        else:
            self.widget_data[0]['employee_name'] = '#Form/Employee/{0}'.format(get_employee_code())

def convert_reward(minutes, shiftHours):
    return {
        'days': int(math.floor(minutes / (60 * shiftHours))),
        'hours': int(math.floor((minutes / 60) % shiftHours)),
        'minutes': int(minutes % 60)
    }

def render_penalty_widget_data():
    result = calculate_penalty_widgets()
    penalties = False
    title = 'Late Penalty Minutes'
    if result['attendance_penalties'][0]:
        record = result['attendance_penalties'][0]

        if record['policy_multiplier'] is None:
            record['policy_multiplier'] = 0

        penalties = int(record['total_late_arrival']) * float(record['policy_multiplier'])
        # show remaining minutes
        if record['policy_multiplier'] == 0:
            title = 'Remaining Minutes'

    count = penalties
    if penalties == False:
        count = 0
    # not to show 0 days penalty in case of 0 penalties
    if count == 0:
        if result['attendance_penalties'][0]['policy_unit_value_to'] is None:
            result['attendance_penalties'][0]['policy_unit_value_to'] = 0
        count = int(result['attendance_penalties'][0]['policy_unit_value_to']) - int(
            result['attendance_penalties'][0]['total_late_arrival'])
    count = str(count) + " <span class='font-size-15'>(mins)</span>"
    total_late_arrival = total_late_instance = 0
    if result['attendance_penalties'][0]['total_late_arrival']:
        total_late_arrival = result['attendance_penalties'][0]['total_late_arrival']

    if result['attendance_penalties'][0]['total_late_instance']:
        total_late_instance = result['attendance_penalties'][0]['total_late_instance']

    return [{'minutes': total_late_arrival, 'instances': total_late_instance, 'title': title, 'total': count}]

# Calculate the Penalty Widgets
def calculate_penalty_widgets():
    result = {}
    userid = get_employee_code()
    date = datetime.datetime.today().strftime('%Y-%m-%d')
    now = datetime.datetime.now()
    if (now.day > _globals.MONTHLY_ATTENDANCE_DATE):
        date = datetime.datetime.today() + relativedelta(months=1)
        date = date.strftime('%Y-%m-%d')
    date_range = getPenaltyDateRange(date)
    start = date_range['month_start_date']
    end = date_range['month_end_date']
    # if attendance data exists it returns array
    attendancepolicies = AttendancePolicies(False)
    if not userid:
        userid = "Administrator"
    records = attendancepolicies.get_employee_policies(start, end, [userid])
    # get policy applied to user and 0 multiplier rule
    if not records:
        records = attendancepolicies.get_user_policies(userid)
        if not records:
            records = [{}]
            records[0]['policy_multiplier'] = None
            records[0]['policy_unit_value_to'] = None
        records[0]['total_late_instance'] = 0
        records[0]['total_late_arrival'] = 0
    result['attendance_penalties'] = records
    return result
