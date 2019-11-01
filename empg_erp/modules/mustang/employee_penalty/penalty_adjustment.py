import frappe
from frappe import _
from datetime import datetime
from empg_erp.modules.common.error_handler import ErrorHandler
from empg_erp.utils import copy_fields
from .attendance_policies import AttendancePolicies

class PenaltyAdjustment():

    def __init__(self):
        pass

    @classmethod
    def reverse_penalty(cls, employee, processed_id):

        attendance_penalty_processed = frappe.get_doc("Attendance Penalties Processed",  processed_id)

        _month = attendance_penalty_processed.month
        _year = attendance_penalty_processed.year

        attendance_penalty_processed.delete()

        if frappe.db.exists("Employee Attendance Penalties", 
            { "employee": employee, "month" : _month, "year" : _year, "type" : "adjustment"}) :
            
            frappe.get_doc(
                "Employee Attendance Penalties", 
                { "employee": employee, "month" : _month, "year" : _year, "type" : "adjustment"}
            ).delete()

        return {"code" : 200, "msg" : "success"}


    def process_adjustment(self, penalty_list):

        penalty_ids = list()
        employee_ids = list()
        indexed_list = dict()
        errors = list()
        year = None
        month = None

        if not frappe.db.exists("Leave Type", "Earned Leave"):
            try:
                doc = frappe.get_doc({
                    "doctype" : "Leave Type",
                    "leave_type_name" : "Earned Leave",
                    "display_name" : "Earned",
                    "is_earned_leave" : 1
                })

                doc.save()
            except Exception as err:
                frappe.throw(_("Unable to create earned leaves type"))
        
        for penalty in penalty_list:
            indexed_list[penalty["id"]] = penalty
            penalty_ids.append(penalty["id"])

        _sql = """
            SELECT ap.year, ap.month, ap.employee, ap.attendance_policy_rules, ap.name
            FROM `tabEmployee Attendance Penalties` ap
            LEFT JOIN `tabAttendance Penalties Processed` app 
            ON app.employee = ap.employee AND app.month = ap.month AND app.year = ap.year
            WHERE app.name IS NULL AND ap.name IN ({})
            GROUP BY ap.employee
        """.format("'" + "','".join(penalty_ids) + "'")

        penalties = frappe.db.sql(_sql, as_dict = True)

        if len(penalties) > 0:

            for penalty in penalties:
                
                employee_ids.append(penalty["employee"])
                year = penalty["year"]
                month = penalty["month"]

                try:
                    if "adjustment" in indexed_list[penalty["name"]] and indexed_list[penalty["name"]]["adjustment"]:
                        
                        adjustment = frappe.get_doc({
                                "doctype" : "Employee Attendance Penalties",
                                "year" : penalty["year"],
                                "month" : penalty["month"],
                                "employee" : penalty['employee'],
                                "value" : (-1 * int(indexed_list[penalty["name"]]["adjustment"])),
                                "penalty" : (-1 * int(indexed_list[penalty["name"]]["adjustment"])),
                                "attendance_policy_rules" : penalty['attendance_policy_rules'],
                                "comments" : 'Adjusted by .',
                                "type" : "adjustment"
                            })

                        adjustment.insert()

                    frappe.get_doc({
                        "doctype" : "Attendance Penalties Processed",
                        "month" : month,
                        "year" : year, 
                        "employee" : penalty["employee"]
                    }).insert()

                except Exception as err:
                    errors.append("{0} ---> {1}.".format(err,penalty["employee"]))  
                    ErrorHandler.log_error(str(err))
            
            att_policies = AttendancePolicies()
            result = att_policies.update_leave_quota(year, month, employee_ids)
            if(result):
                for error in result:
                    errors.append("{0}".format(error))                    
        
        return errors


        