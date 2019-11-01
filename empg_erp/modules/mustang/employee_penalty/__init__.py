from .attendance_penalty import AttendancePenalty
import frappe
from datetime import datetime
import json
from empg_erp.utils import get_monthly_diff_dates, get_date_range
from .penalty_adjustment import PenaltyAdjustment
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE, MONTHLY_ATTENDANCE_START_DATE

# TODO : will create a schedular after complete testing
@frappe.whitelist(allow_guest=True)
def calculate_penalties():

    month = int(datetime.today().strftime("%m"))

    if "month" in frappe.local.form_dict:
        month = int(frappe.local.form_dict["month"])

    date_start, date_end = get_date_range(MONTHLY_ATTENDANCE_START_DATE, MONTHLY_ATTENDANCE_DATE, month)

    att_penalty = AttendancePenalty(date_start, date_end)
    return att_penalty.add_penalties()

@frappe.whitelist()
def adjust_penalties(data):

    penalty_adjustment = PenaltyAdjustment()

    _data = json.loads(data)

    return penalty_adjustment.process_adjustment(_data)


@frappe.whitelist()
def reverse_penalties(employee, processed_id):

    return PenaltyAdjustment.reverse_penalty(employee, processed_id)

def reprocess_negative_penalties():
    _sql = """
    SELECT 
        pp.name as penalty_processed,
        ap.name as penalty,
        la.employee        
    FROM 
        `tabLeave Application` la
    INNER JOIN
        `tabEmployee Penalty Leaves` pl 
        ON 
            la.name = pl.leave_application
    INNER JOIN
        `tabAttendance Penalties Processed` pp 
        ON 
            pl.attendance_penalties_processed = pp.name
    INNER JOIN 
        `tabEmployee Attendance Penalties` ap 
        ON 
            pp.year = ap.year AND pp.month = ap.month AND pp.employee = ap.employee
    WHERE 
        la.total_leave_days > la.leave_balance
        AND la.description = 'Penalty Deduction'
        AND la.docstatus=1
        AND YEAR(la.creation) = YEAR(CURDATE()) AND MONTH(la.creation) > 03
        AND STATUS='Approved'
    """
    penalties = frappe.db.sql(_sql, as_dict = True)
    penalties_arr = list()
    if(penalties):        
        for penalty in penalties:
            try:
                reverse_penalties(penalty["employee"],penalty["penalty_processed"])
                penalties_arr.append({"id":penalty["penalty"]})
                print(penalty["penalty"])
                print("============Reversed==============")
            except Exception as err:
                print(err)

    penalty_adjustment = PenaltyAdjustment()
    for penalty in penalties_arr:
        result = penalty_adjustment.process_adjustment([penalty])
        print(penalty)
        print("============Processed==============")

