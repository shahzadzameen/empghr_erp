import frappe
from frappe import _
from empg_erp.constants.table_names import EMP_ATT_PENALTIES, ATT_POLICY_RULES, \
EMP_ATT_ASSOCIATION, ATT_POLICY
from empg_erp.utils import get_table_name, unlock_doc, get_monthly_diff_dates,\
get_config_by_name,get_report_to,str_to_date
from datetime import datetime, timedelta
import math
from frappe.model.naming import set_name_by_naming_series
from empg_erp.modules.mustang.leave_application.leave_application import get_leave_details, get_leave_allocation_detail
from empg_erp.modules.common.error_handler import ErrorHandler

class AttendancePolicies():

    def __init__(self, exclude_employee = True):
        self.exclude_employee = exclude_employee

    def get_user_policies(self, userid):

        _sql = """
               SELECT `pa`.*, `p`.*, `pr`.`name` AS `policy_rule_id`, `pr`.`policy_multiplier`, `pr`.`policy_unit`, 
               `pr`.`unit_value_to` AS `policy_unit_value_to` 
               FROM `{2}` AS `pa`
                LEFT JOIN `{0}` AS `p` ON pa.attendance_policy = p.name
                LEFT JOIN `{1}` AS `pr` ON pa.attendance_policy = pr.attendance_policy AND pr.policy_multiplier = 0 WHERE (pa.employee = %s)
           """.format(get_table_name(ATT_POLICY), get_table_name(ATT_POLICY_RULES), get_table_name(EMP_ATT_ASSOCIATION))

        return frappe.db.sql(_sql, [userid], as_dict=True)

    def get_employee_policies(self, start_date, end_date, employees = []):
        _ids = []
        employee_exclude_ids = ""
        employee_ids = ""

        if len(employees) > 0:
            employee_ids = "AND ea.employee IN ('" + "', '".join(str(i) for i in employees) + "')"

        if self.exclude_employee:

            employee_exc_list = self.get_employees(end_date)

            for employee in employee_exc_list:
                _ids.append(employee["employee"])

            if len(_ids) > 0:
                employee_exclude_ids = "AND `ea`.`employee` NOT IN ('" + "', '".join(_ids) + "')"


        # TODO : break this query
        # calculate total late arrival separately
        # check holidays separately

        _sql ="""
            SELECT 
            `t`.`name`,
            `t`.`attendance_date`,
            `t`.`late_arrival` AS `total_late_instance`,
            `t`.`late_arrival_total` AS `total_late_arrival`,
            `p`.`policy_type`,
            `p`.`name` AS `policy_id`,
            `pr`.`name` AS `policy_rule_id`,
            `pr`.`policy_multiplier`,
            `pr`.`policy_unit`,
            `pr`.`unit_value_to` AS `policy_unit_value_to`,
            `p`.`allow_penalty_deduction`,
            `p`.`allow_reward`
            FROM
                (SELECT 
                `e`.`name`,
                lr.status,
                `ea`.`attendance_date`,
                COUNT(
                IF(
                ea.late_arrival > 0
                AND (lr.status is NULL OR lr.status != "approved")
                AND ((h.holiday_date IS NULL
                AND ch.holiday_date IS NULL
                AND erch.holiday_date IS NULL) OR eas.consider_penalty = 1),
                ea.late_arrival, NULL)) AS `late_arrival`,
                
                SUM(IF(ea.late_arrival > 0 
                AND (lr.status is NULL OR lr.status != "approved")
                AND ((h.holiday_date IS NULL
                AND ch.holiday_date IS NULL
                AND erch.holiday_date IS NULL) OR eas.consider_penalty = 1),
                ea.late_arrival, 0)) AS `late_arrival_total`

                FROM `tabAttendance` AS `ea`
                LEFT JOIN `tabRoster Status` eas ON eas.name = ea.attendance_Status
                LEFT JOIN `tabEmployee` AS `e` ON ea.employee = e.employee
                LEFT JOIN `tabShift Type` st ON e.shift_type = st.name
            
                LEFT JOIN `tabLeave Application` AS `lr` ON ea.employee = lr.`employee`
                    AND ea.attendance_date BETWEEN lr.from_date AND lr.to_date
                    AND lr.docstatus = 1 AND lr.status = "Approved"
                LEFT JOIN
                `tabHoliday List` hl ON hl.name = e.holiday_list
                LEFT JOIN
                `tabHoliday` h ON h.parent = hl.name AND h.holiday_date = ea.attendance_date
                LEFT JOIN
                `tabCompany` c ON c.name = e.company
                LEFT JOIN
                `tabHoliday List` chl ON chl.name = c.default_holiday_list
                LEFT JOIN
                `tabHoliday` ch ON ch.parent = chl.name AND ch.holiday_date = ea.attendance_date
                LEFT JOIN
                `tabHoliday List` erhl ON erhl.name = st.holiday_list
                LEFT JOIN
                `tabHoliday` erch ON erch.parent = erhl.name AND erch.holiday_date = ea.attendance_date

                WHERE
                    ea.docstatus = 1
                    AND ea.attendance_date >= '{0}'
                    AND ea.attendance_date <= '{1}'
                    AND ea.name IS NOT NULL
                    AND eas.consider_penalty = 1
                    {2}
                    {6}
                GROUP BY `ea`.`employee`
                ORDER BY `ea`.`attendance_date` ASC) AS `t`
                INNER JOIN
                `{3}` AS `pa` ON t.name = pa.employee
                INNER JOIN
                `{4}` AS `p` ON pa.`attendance_policy` = p.name
                INNER JOIN
                `{5}` AS `pr` ON pr.attendance_policy = p.name
                    AND pr.unit_value_from <= t.late_arrival_total
                    AND pr.unit_value_to >= t.late_arrival_total
                GROUP BY `t`.`name`
            """.format(
                start_date, end_date, employee_exclude_ids, 
                get_table_name(EMP_ATT_ASSOCIATION),
                get_table_name(ATT_POLICY),
                get_table_name(ATT_POLICY_RULES),
                employee_ids
                )
        return frappe.db.sql(_sql, as_dict=True)


    def get_user_with_policies(self, start_date, end_date):

        return self.get_employee_policies(start_date, end_date)

    def get_employees(self, date):

        _date = datetime.strptime(date, "%Y-%m-%d")

        year = datetime.strftime(_date, "%Y")
        month = datetime.strftime(_date, "%m")

        employee_list = frappe.db.sql(
            """
            SELECT employee FROM `{0}`
            WHERE year = '{1}' AND month = '{2}'
            """.format(get_table_name(EMP_ATT_PENALTIES), year, month),
            as_dict=True
        )

        return employee_list

    def update_leave_quota(self, year, month, employee_ids):
        errors = list()
        if len(employee_ids) == 0:

            return False

        _df_start_time = get_config_by_name("default_shift_start_time", "09:00:00")
        _df_end_time = get_config_by_name("default_shift_end_time", "18:00:00")

        _sql = """
            SELECT 
                `eap`.*,
                SUM(eap.penalty) AS `calculated_val`,
                app.name as processed_id,
                `apr`.*,
                `emp`.`department`,
                `emp`.`employee_name`,
                `emp`.`date_of_joining`,
                HOUR(TIMEDIFF(
                if(shift.end_time IS NOT NULL,shift.end_time, "{3}"),
                if(shift.start_time IS NOT NULL,shift.start_time, "{4}")
                )) as working_hours
            FROM
                `tabEmployee Attendance Penalties` AS `eap`
                INNER JOIN `tabAttendance Policy Rules` AS `apr` ON eap.attendance_policy_rules = apr.name
                INNER JOIN `tabEmployee` AS `emp` ON eap.employee = emp.employee
				LEFT JOIN `tabShift Type` as shift ON shift.name = emp.shift_type
                LEFT JOIN `tabAttendance Penalties Processed` app on app.employee = emp.employee
                AND app.month = eap.month AND app.year = eap.year
                
            WHERE
                (eap.year = '{0}' AND eap.month = '{1}'
                    AND eap.employee IN ({2}))
            GROUP BY `eap`.`employee`  
        """.format(year, month, "'" + "','".join(employee_ids) + "'", _df_end_time, _df_start_time)

        employee_list = frappe.db.sql(_sql, as_dict=True)
        
        date_start = datetime.today()
        from_date = posting_date = str_to_date(date_start, "%Y-%m-%d")
        month_start_date = str_to_date(datetime(int(year), int(month), 01),'%Y-%m-%d')

        for emp in employee_list:

            penalty_min = emp["calculated_val"]
            penalty_days = round((penalty_min/60) / int(emp["working_hours"]) , 2)

            response = self.create_earned_leave_quota(emp["employee"])
            if(response):
                errors.append("{0} ---> {1}.".format(response,emp["employee"]))
                continue

            if emp["policy_multiplier"] > 0:

                _itr = 20
                date_of_joining = str_to_date(emp["date_of_joining"],'%Y-%m-%d')
                if(date_of_joining > month_start_date):
                    month_start_date = date_of_joining

                while penalty_days > 0 and _itr > 0:

                    leaves = self.get_prioritized_pending_leaves(emp["employee"], month_start_date)
                    
                    if bool(leaves):

                        _quota = 0

                        if leaves["remaining_leaves"] <= 0 :
                            break

                        elif leaves["remaining_leaves"] > penalty_days:
                            _quota = penalty_days
                            penalty_days = 0
                        else:
                            # if remaining leaves < penalty days
                            _quota = leaves["remaining_leaves"]
                            penalty_days = penalty_days - leaves["remaining_leaves"]

                        to_date = datetime.strftime(month_start_date + timedelta(days=math.ceil(_quota) -1), "%Y-%m-%d")

                        try :

                            leave_application = frappe.get_doc({"doctype" : "Leave Application"})
                            set_name_by_naming_series(leave_application)
                            leave_approver = get_report_to(emp["employee"],True)

                            _sql = """
                                INSERT INTO `tabLeave Application` (name, employee, employee_name, from_date, to_date, status,
                                total_leave_days, docstatus, leave_type, description, department, leave_balance, follow_via_email, leave_approver, posting_date, creation, modified) 
                                VALUES ("{}", "{}", "{}", "{}", "{}", "Approved", "{}", 1, "{}", "Penalty Deduction", "{}", "{}", 0, "{}", "{}", NOW(), NOW() )
                                """.format(leave_application.name, emp["employee"], emp["employee_name"], month_start_date, to_date, _quota, 
                                leaves["leave_type"], emp["department"], leaves["leave_balance"],leave_approver ,posting_date)

                            frappe.db.sql(_sql)

                        except Exception as err:
                            frappe.log_error(err)
                            errors.append("{0} ---> {1}.".format(_("Unable to update quota"),emp["employee"]))
                            break
                        try :

                            frappe.get_doc({
                                "doctype" : "Employee Penalty Leaves",
                                "leave_application" : leave_application.name,
                                "attendance_penalties_processed" : emp["processed_id"]
                            }).submit()

                        except Exception as err:
                            frappe.log_error(err)
                            errors.append("{0} ---> {1}.".format(_("Unable to log quota updation"),emp["employee"]))
                            break
                    else:
                        errors.append("{0} ---> {1}.".format(_("didn't find any leave to deduct quota"),emp["employee"]))
                        break
                    _itr -= 1

            else:

                reward_minutes = emp["unit_value_to"] - emp["value"]
                reward_days = round(float(reward_minutes/60) / int(emp["working_hours"]) , 2)

                start_date, end_date = get_monthly_diff_dates()

                earned_leaves = get_leave_allocation_detail(emp["employee"], "Earned Leave", start_date, end_date)

                if len(earned_leaves) > 0:
                    
                    try :

                        leave_allocation = frappe.get_doc("Leave Allocation", earned_leaves[0]["name"])
                        
                        leave_allocation_log = frappe.get_doc({
                            "doctype" : "Leave Allocation Log",
                        })

                        leave_allocation_log.total_leaves_allocated = leave_allocation.total_leaves_allocated
                        leave_allocation_log.employee = leave_allocation.employee
                        leave_allocation_log.leave_type = leave_allocation.leave_type
                        leave_allocation_log.to_date = leave_allocation.to_date
                        leave_allocation_log.from_date = leave_allocation.from_date

                        leave_allocation_log.insert()

                        leave_allocation.update({"new_leaves_allocated": float(reward_days) + float(earned_leaves[0]["total_leaves_allocated"])})
                        leave_allocation.flags.ignore_permissions = True
                        leave_allocation.save()

                    except Exception as err:
                        errors.append("{0} ---> {1}.".format(_("Unable to update quota"),emp["employee"]))                     

        return errors

    def create_earned_leave_quota(self, employee):
        err = False
        try:
            _year = datetime.today().strftime("%Y")

            from_date = "{0}-01-01".format(_year)
            to_date = "{0}-12-31".format(_year)
            leave_allocation = frappe.db.sql("""
                select name from `tabLeave Allocation`
                where employee=%s and leave_type=%s and docstatus=1
                and to_date >= %s and from_date <= %s""",
                (employee, "Earned Leave", from_date, to_date))
            
            if not leave_allocation:
                earned_leaves = frappe.get_doc({
                    "doctype" : "Leave Allocation",
                    "leave_type" : "Earned Leave",
                    "employee" : employee,
                    "docstatus" : 1,
                    "new_leaves_allocated" : 0,
                    "total_leaves_allocated" : 0
                })

                earned_leaves.from_date = from_date
                earned_leaves.to_date = to_date

                earned_leaves.save()
        except Exception as err:
            err = _("Unable to create earned leaves quota")
        return err

    def get_prioritized_pending_leaves(self, emp, date_start):

        _pending_leaves = get_leave_details(emp, date_start)
        _from_date = None
        _quota_type = None
        _remaining_leaves = 0
        _leave_balance = 0

        _quota_pr = frappe.db.get_all("Quota Deduction Priority", {}, "*", order_by="precedence")

        for quota in _quota_pr:

            if quota["leave_type"] in _pending_leaves["leave_allocation"] :
                
                if _pending_leaves["leave_allocation"][quota["leave_type"]]["remaining_leaves"] > 0 :
                    
                    _leave_allocation = frappe.get_all(
                        "Leave Allocation", {"to_date" : [">=", date_start],"employee" : emp, "leave_type" : quota["leave_type"] }, 
                        ["from_date"]
                        )

                    if len(_leave_allocation) > 0:
                        _from_date = _leave_allocation[0]["from_date"]

                    _quota_type = quota["leave_type"]
                    _leaves = _pending_leaves["leave_allocation"][quota["leave_type"]]
                    _remaining_leaves = _pending_leaves["leave_allocation"][quota["leave_type"]]["remaining_leaves"] 
                    _leave_balance = float(_leaves["total_leaves"]) - float(_leaves["leaves_taken"])

                    break

        if not _quota_type:
            return None

        return {
                    "from_date" : _from_date,
                    "leave_type" : _quota_type,
                    "remaining_leaves" : _remaining_leaves,
                    "leave_balance" : _leave_balance
                }

        
