from datetime import datetime
import frappe
from .attendance_policies import AttendancePolicies
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.constants.globals import POLICY_TYPE_PENALTY, POLICY_TYPE_REWARD

class AttendancePenalty():

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def add_penalties(self):

        att_polices = AttendancePolicies()

        employee_list = att_polices.get_user_with_policies(self.start_date, self.end_date)
        for employee in employee_list:
            self.calculate_non_aggregative(employee, self.end_date)

        frappe.db.commit()

        return "successfully updated"

    def calculate_employee_penalties(self, employee):

        # refetch penalties if already calculated
        att_polices = AttendancePolicies(False)
        employees = [employee]

        employee_list = att_polices.get_employee_policies(self.start_date, self.end_date, employees)
        
        for employee in employee_list:
            self.update_non_aggregative(employee, self.end_date)

        return "successfully updated"


    def calculate_non_aggregative(self, employee, date):
        
        _date = datetime.strptime(date, "%Y-%m-%d")
        year = datetime.strftime(_date, "%Y")
        month = datetime.strftime(_date, "%m")
        _type = POLICY_TYPE_REWARD

        if employee['policy_multiplier'] > 0:
            _type = POLICY_TYPE_PENALTY
        
        """
        check if type penalty and allow penalty not is marked or
        check if type reward and allow reward not is not marked then dont add record 
        """

        if ( _type == POLICY_TYPE_PENALTY and bool(employee["allow_penalty_deduction"]) == False \
            or _type == POLICY_TYPE_REWARD and bool(employee["allow_reward"]) == False):
            return False

        try:
            
            penalty = frappe.get_doc({
                    "doctype" : "Employee Attendance Penalties",
                    "year" : year,
                    "month" : month,
                    "employee" : employee['name'],
                    "value" : employee['total_late_arrival'],
                    "penalty" : (employee['total_late_arrival'] * employee['policy_multiplier']),
                    "instance" : employee['total_late_instance'],
                    "attendance_policy_rules" : employee['policy_rule_id'],
                    "type" : _type,
                    "comments" : 'added by script'
                })

            penalty.insert()

            return penalty
            
        except Exception as err:
            ErrorHandler.log_error(str(err))

    def update_non_aggregative(self, employee, date):
        
        _date = datetime.strptime(date, "%Y-%m-%d")
        year = int(datetime.strftime(_date, "%Y"))
        month = int(datetime.strftime(_date, "%m"))

        penalty_list = frappe.get_all("Employee Attendance Penalties", {
            "year" : year,
            "month" : month,
            "employee" : employee['name'],
            "type" : "penalty"
        }, ["name"])

        if len(penalty_list) == 0:
            return {}

        try:

            penalty = frappe.get_doc("Employee Attendance Penalties", penalty_list[0]["name"])

            if(penalty):
                penalty.value = employee['total_late_arrival']
                penalty.penalty = (employee['total_late_arrival'] * employee['policy_multiplier'])
                penalty.instance = employee['total_late_instance']
                penalty.attendance_policy_rules = employee['policy_rule_id']
                
                penalty.save()

            return penalty
            
        except Exception as err:
            ErrorHandler.log_error(str(err))