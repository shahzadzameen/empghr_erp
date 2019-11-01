# Copyright (c) 2013, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import time

import frappe
from datetime import datetime
from empg_erp.utils import get_months_and_year
from empg_erp.modules.mustang.employee.employee_roster import EmployeeRoster
import json
import math
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE, PAGE_SIZE, LINE_MANAGER, HR_USER, HR_MANAGER, ADMINISTRATOR, EMPLOYEE
from empg_erp.utils import get_user_role, check_advance_privilege_by_name, get_config_by_name
from empg_erp.utils import get_auth_team_ids, get_user_filters_by_role


def execute(filters=None):
    if filters.get("page"):
        concat = str(filters.get("page")).split('_')
        limit = str(concat[0])
    else:
        limit = str(PAGE_SIZE)

    limit = " LIMIT " + limit
    limit_hidden = str(filters.get("page"))
    if limit_hidden == 'None':
        limit_hidden = str(PAGE_SIZE)

    _filters = get_condition(filters)
    data = []

    employee_data, totalRecords = getAttendanceAdjustment(_filters, limit)

    for emp in employee_data:

        row = []
        employeeId = emp["employee"]
        adjusted_penalty = None
        
        if emp["adjusted_penalty"] > 0 and emp["working_hours"]:
            adjusted_penalty = round((emp["adjusted_penalty"]/60)/int(emp["working_hours"]), 2)

        if emp["processed"]:
            row.append(penalties_actions(employeeId, "disabled", emp["name"]))
        else:
            row.append(penalties_actions(employeeId, "", emp["name"]))

        row.append(employeeId)
        row.append(emp["employee_name"])
        row.append(emp["month"])
        row.append(emp["instance"])

        row.append(emp["minutes"])
        
        if emp["penalty"] > 0:
            row.append(emp["penalty"])
        else:
            row.append(emp["reward_minutes"])

        if emp["processed"] or emp["penalty"] == 0:
            row.append(emp["adjustment"])
        else:
            row.append(get_adjustment_box(employeeId))

        row.append(get_adjusted_penalty(emp["adjusted_penalty"], employeeId))

        if emp["penalty_deducted"] and emp["penalty"] > 0:
            row.append(emp["penalty_deducted"])
        else:
            row.append("-")

        if isinstance(emp["penalty_deducted"],  float) and emp["processed"] and adjusted_penalty:
            row.append(round(float(adjusted_penalty) - float(emp["penalty_deducted"]), 2))
        else:
            row.append("-")

        if emp["processed"] and emp["penalty"] > 0:
            row.append(get_reversal_button(employeeId, emp["processed_id"], datetime(emp["year"], emp["month"], 01).date()))
        elif emp["processed"] and emp["penalty"] <= 0 :
            row.append("Processed")
        else:
            row.append(get_adjustment_button(employeeId, emp["name"], emp["reward_minutes"]))

        data.append(row)

    columns = [(
                "<input type='checkbox'  class='selectall' name='select_all' onclick='select_all_checkbox(this," + '10037' + ")'> </input>""") + "::60",
               ("Code<input type='hidden' value='" + limit_hidden + "' id='page' />") + "::100", ("Employee") + "::180",
               ("Month") + "::80", ("Instances") + "::80",
               ("Arrived Late By(mins)") + "::80", ("Penalty/Reward(mins") + "::80", ("Adjustment(mins)") + "::100",
               ("Adjusted(mins)") + "::80", ("Penalty Deducted(days)") + "::140", ("Penalty Left(days)") + "::140","Process" + "::85"]
    return columns, data


def get_condition(filters):
    cond = dict()

    if "page" in filters:
        del (filters["page"])

    if bool(filters) == False:
        return ""
    if "month" in filters:
        _datetime = datetime.strptime(filters["month"], "%b,%Y")
        cond["etp.year"] = datetime.strftime(_datetime, "%Y")
        cond["etp.month"] = datetime.strftime(_datetime, "%m")

    if "department" in filters:
        cond["e.department"] = filters["department"]

    if "sub_department" in filters:
        cond["e.sub_department"] = filters["sub_department"]

    if "city" in filters:
        cond["e.office_city"] = filters["city"]
        
    if "employee" in filters:
        cond["etp.employee"] = filters["employee"]

    _cond = ""
    if cond:
        _cond = " WHERE " + " AND ".join("{} = '{}'".format(key, value) for key, value in cond.items())

    if "type" in filters:
        if filters.get("type") != "Select Type":
            if filters.get("type") == "Reward":
                _cond += " AND pr.policy_multiplier = 0 AND (pr.unit_value_to - etp.value) > 0 "
            if filters.get("type") == "Penalty":
                _cond += " AND pr.policy_multiplier != 0 "

    if "status" in filters:
        if filters.get("status") != "Select Status":
            if filters.get("status") == "Processed":
                _cond += " AND app.name IS NOT NULL"
            elif filters.get("status") == "Unprocessed":
                _cond += " AND app.name IS NULL"
    return _cond


def penalties_actions(emp_id, disable, penalty_id):
    return "<input type='checkbox' class='individual' name='emp_action_check' " + disable + "  value=" + penalty_id + "  id=" + emp_id + ">"


def get_adjustment_box(emp_id):
    return "<input type='text'  onkeypress='return (event.charCode == 8 || event.charCode == 0 || event.charCode == 13) ? null : event.charCode >= 48 && event.charCode <= 57' class='reportInput penalty-adjustment-{0}' name='emp_action_text' id='{0}'>".format(
        emp_id)


def get_adjustment_button(emp_id, penalty_id, reward_minutes):
    process_text = "Process"
    if reward_minutes > 0:
        process_text = "Reward"
    return """<button type="button" class="btn-primary btn btn-sm process-style" onclick="process_penalty('{0}','{1}')">{2}</button>""".format(
        emp_id, penalty_id, process_text)

def get_reversal_button(emp_id, processed_id, attendance_date):

    if (check_advance_privilege_by_name(get_config_by_name('CAN_REVERSE_ATTENDANCE_PENALTY')) == False
    or  EmployeeRoster.is_cutoff_passed(attendance_date, get_config_by_name('PENALTY_REVERSAL_MONTHS_LIMIT',2))  == True):
        return "Processed"
    else:
        return """<button type="button" class="btn-primary btn btn-sm process-style" onclick="reverse_penalty('{0}','{1}')">{2}</button>""".format(
            emp_id, processed_id, "Reverse")


def get_adjusted_penalty(adjustedPenalty, emp_id):
    return "<span title='{0}' class='adjusted-penalty{1} pull-right'>{0}</span>".format(adjustedPenalty, emp_id)


@frappe.whitelist()
def getOnloadData():
    months = get_months_and_year()
    return months


@frappe.whitelist()
def getPaginationData(filters):
    filters = json.loads(filters)
    advances_list = get_condition(filters)
    adjustment_data, totalRecords = getAttendanceAdjustment(advances_list, "")
    pagination = getPages(totalRecords, PAGE_SIZE)
    filtersData = {'pagination': pagination, "totalRecords": totalRecords}
    return filtersData


def getAttendanceAdjustment(_filters, limit):
    _sql = """
		SELECT 
         IF(penalty_deducted.penalty_deducted IS NULL AND app.name, 0, penalty_deducted.penalty_deducted) as penalty_deducted,
         TIMESTAMPDIFF(HOUR,
         st.start_time,
         IF(st.end_time < st.start_time, st.end_time + INTERVAL 24 HOUR, st.end_time)
         ) as working_hours,
         etp.name, etp.value, etp.employee, etp.year, etp.month,etp.type,
 		e.department,e.employee_name, app.name as processed_id,
 		SUM(IF(etp.value >= 0, etp.value, 0)) AS `minutes`,
         SUM(IF(etp.`type` = 'penalty',etp.`instance`,0)) AS instance,    
  		SUM(IF(etp.`type` = 'penalty',etp.`penalty`,0)) AS penalty,
 		ABS(SUM(IF(etp.`type` = 'adjustment',etp.`value`,0))) AS adjustment,
 		IF(app.name is NOT NULL, true, false) as processed,
 		IF(pr.policy_multiplier = 0,
 				(pr.unit_value_to - etp.value),
 				0) AS `reward_minutes`,
 		SUM(etp.penalty) AS `adjusted_penalty`
 		FROM `tabEmployee Attendance Penalties` as etp
 		LEFT JOIN `tabEmployee` as e ON e.employee = etp.employee
         LEFT JOIN `tabShift Type` as st on st.name = e.shift_type
 		LEFT JOIN `tabAttendance Policy Rules` AS `pr` ON pr.name = etp.attendance_policy_rules
 		LEFT JOIN `tabAttendance Penalties Processed` as app ON app.employee = etp.employee
 		AND app.year = etp.year AND app.month = etp.month
		LEFT JOIN (SELECT SUM(la.total_leave_days) as penalty_deducted, attendance_penalties_processed
         FROM `tabEmployee Penalty Leaves` as epl 
        LEFT JOIN `tabLeave Application` as la
        ON epl.leave_application = la.name AND la.docstatus = 1 AND la.status = "Approved"
        WHERE epl.docstatus = 1
        GROUP BY attendance_penalties_processed) as penalty_deducted
        ON penalty_deducted.attendance_penalties_processed = app.name
        {0}
 		GROUP BY etp.employee
 		ORDER BY instance DESC
		{1}
		""".format(_filters, limit)
    adjustment_data = frappe.db.sql(_sql, as_dict=True)

    return adjustment_data, len(adjustment_data)


def getPages(totalRecords, pageSize):
    pagination = ["1"]
    if pageSize > 0 and totalRecords > 1:
        totalPages = (totalRecords * 1.0) / pageSize
        totalPages = int(math.ceil(totalPages))
        pagination = range(1, totalPages + 1)
    return pagination