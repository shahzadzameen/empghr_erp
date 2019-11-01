import frappe, json, hashlib, calendar
from datetime import datetime, timedelta, date
from .employee_attendance import EmployeeAttendance
from empg_erp.modules.mustang.shift import get_employee_shift
from empg_erp.constants.table_names import ZKTEKO_LOG
from empg_erp.utils import get_time_diff, get_timestamp, unlock_doc
from empg_erp.modules.common.error_handler import ErrorHandler

class AttendanceCalculation():

    MIN_EARLY = 0
    MAX_LATE = 0
    GRACE_MINS = 0
    EMPLOYEE_PREFIX = ""

    def __init__(self, emp_id):

        #self.emp_id = "{0}{1}".format(self.EMPLOYEE_PREFIX, emp_id)
        self.emp_id = emp_id
        self.attendance_date = None
        self.attendance_time = None
        self.attendance_datetime = None
        self.prev_date = None


    def prev_attendance(self, indexed_list, prev_shift_start, prev_shift_end, emp_shift, today_shift_start):

        min_checkout = min_checkin = datetime.strptime(prev_shift_start, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=self.MIN_EARLY)
        max_checkin = datetime.strptime(prev_shift_end, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=60)

        max_checkout = datetime.strptime(prev_shift_end, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=self.MAX_LATE)

        emp_att = EmployeeAttendance()

        if get_timestamp(prev_shift_end) >= get_timestamp(self.attendance_datetime) or\
           get_timestamp(max_checkout) >= get_timestamp(self.attendance_datetime):

            prev_att_data = indexed_list[self.prev_date]

            emp_att.check_out = self.attendance_datetime
            emp_att.left_early = get_time_diff(prev_shift_end,self.attendance_datetime, "mins")
            emp_att.working_hours= get_time_diff(self.attendance_datetime,prev_att_data["check_in"], "hours")

            return self.add_update_doc(emp_att, prev_att_data["name"])
        else:

            emp_att.employee = self.emp_id
            # emp_att.shift = emp_shift.name
            emp_att.grace_mins = self.GRACE_MINS
            emp_att.attendance_date = self.attendance_date
            emp_att.check_in = self.attendance_datetime
            emp_att.shift_start_time = emp_shift.start_time
            emp_att.shift_end_time = emp_shift.end_time
            emp_att.late_arrival = get_time_diff(self.attendance_datetime,today_shift_start, "mins")

            return self.add_update_doc(emp_att)

    def new_attendance(self, today_shift_start, prev_shift_start, prev_shift_end, emp_shift_prev, emp_shift):

        emp_att = EmployeeAttendance()

        if get_timestamp(self.attendance_datetime) >= get_timestamp(prev_shift_start) and\
           get_timestamp(self.attendance_datetime) <= get_timestamp(prev_shift_end):

            emp_att.employee = self.emp_id
            # emp_att.shift = emp_shift_prev.name
            emp_att.grace_mins = self.GRACE_MINS
            emp_att.attendance_date = self.prev_date
            emp_att.check_in = self.attendance_datetime
            emp_att.shift_start_time = emp_shift.start_time
            emp_att.shift_end_time = emp_shift.end_time
            emp_att.late_arrival = get_time_diff(self.attendance_datetime,prev_shift_start, "mins")
            
            return self.add_update_doc(emp_att)

        else:

            emp_att.employee = self.emp_id
            # emp_att.shift = emp_shift.name
            emp_att.grace_mins = self.GRACE_MINS
            emp_att.attendance_date = self.attendance_date
            emp_att.check_in = self.attendance_datetime
            emp_att.shift_start_time = emp_shift.start_time
            emp_att.shift_end_time = emp_shift.end_time
            emp_att.late_arrival = get_time_diff(self.attendance_datetime,today_shift_start, "mins")

            return self.add_update_doc(emp_att)
        
    def current_attendance(self, indexed_list, today_shift_start, today_shift_end, prev_shift_end):
        
        today_attendance = indexed_list[self.attendance_date]
        min_checkout = min_checkin = datetime.strptime(today_shift_start, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=self.MIN_EARLY)
        max_checkin = datetime.strptime(today_shift_end, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=60)

        prev_max_checkout = datetime.strptime(prev_shift_end, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=self.MAX_LATE)

        emp_att = EmployeeAttendance()

        att_id = today_attendance["name"]

        if get_timestamp(self.attendance_datetime) <= get_timestamp(today_attendance["check_in"]) or \
            today_attendance["check_in"] is None:

            if get_timestamp(self.attendance_datetime) >= get_timestamp(min_checkin) and\
               get_timestamp(self.attendance_datetime) <= get_timestamp(max_checkin):

                emp_att.check_in = self.attendance_datetime
                emp_att.late_arrival = get_time_diff(self.attendance_datetime, today_shift_start, "mins")

                if today_attendance["check_in"]:
                    emp_att.check_out = today_attendance["check_in"]
                    emp_att.left_early = get_time_diff(today_shift_end, emp_att.check_out, "mins")
                    emp_att.working_hours = get_time_diff(emp_att.check_out, emp_att.check_in, "hours" )

            else:

                if str(self.prev_date) in indexed_list and indexed_list[self.prev_date]["check_out"] == None \
                    and indexed_list[self.prev_date]["check_in"] != None \
                    and get_timestamp(self.attendance_datetime) <= get_timestamp(prev_max_checkout):

                    att_id = indexed_list[self.prev_date]["name"]
                    
                    emp_att.check_out = self.attendance_datetime
                    emp_att.left_early = get_time_diff(prev_shift_end,self.attendance_datetime, "mins")
                    emp_att.working_hours= get_time_diff(self.attendance_datetime, indexed_list[str(self.prev_date)]["check_in"], "hours")

                else:
                   
                    emp_att.check_in = self.attendance_datetime
                    emp_att.late_arrival = get_time_diff(self.attendance_datetime,today_shift_start,"mins" )
                    
                    if today_attendance["check_in"]:
                        emp_att.check_out = today_attendance["check_in"]
                        emp_att.left_early = get_time_diff(today_shift_end, emp_att.check_out, "mins")
                        emp_att.working_hours= get_time_diff(emp_att.check_out, emp_att.check_in, "hours")
        
        else:
                
            emp_att.check_out = self.attendance_datetime
            emp_att.left_early = get_time_diff(today_shift_end,self.attendance_datetime, "mins")
            emp_att.working_hours= get_time_diff(self.attendance_datetime,today_attendance["check_in"], "hours")       

        return self.add_update_doc(emp_att, att_id)

    def is_duplicate(self, att_hash):

        att_data = frappe.db.get_all(ZKTEKO_LOG, {"hash" : att_hash}, ["name"])
        if len(att_data) > 0:
            return att_data[0]
        else:
            return None

    def add_update_doc(self, employee, att_id = None):

        attendance = None

        if att_id != None:

            # because document with doc status 1 cannot be updated
            unlock_doc("Attendance", att_id)

            try:

                # updating attendance document with updated attributes
                attendance = frappe.get_doc("Attendance", att_id)

                for attr, value in employee.__dict__.iteritems():
                    if(value != None):
                        attendance.__dict__[attr] = value

                attendance.save()
            except Exception as err:

                ErrorHandler.log_error(str(err))
                return {"error" : err}

        else:

            data = dict()
            data["doctype"] = "Attendance"

            try:

                for attr, value in employee.__dict__.iteritems():
                    if(value != None):
                        data[attr] = value

                attendance = frappe.get_doc(data)

                attendance.insert()
            except Exception as err:
                
                ErrorHandler.log_error(str(err))
                return {"error" : err}
        
        return {"success" : attendance}


    def log_attendance(self, hash, data):
        
        frappe.get_doc({
            "doctype" : ZKTEKO_LOG,
            "hash" : hash,
            "hash_data" : data
        }).save()

    def get_err_object(self, msg, att_data, code = 500):

        return {
                "data_id" : att_data["id"] if "id" in att_data else None,
                "name" : self.emp_id,
                "code" : code,
                "message" : msg,
                "list_item" : []
            }

    def get_shift_start_end(self, attendance_date, emp_shift):
        
        today_shift_start = "{0} {1}".format(attendance_date, emp_shift.start_time)
        today_shift_end = "{0} {1}".format(attendance_date, emp_shift.end_time)

        if get_timestamp(today_shift_end) < get_timestamp(today_shift_start):
            _shift_start = datetime.strptime(today_shift_end, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
            today_shift_end = datetime.strftime(_shift_start, "%Y-%m-%d %H:%M:%S")
        
        return today_shift_start, today_shift_end

  
    def add_update_attendance(self, att_data):
        
        result = list()

        att_hash = hashlib.md5(json.dumps(att_data)).hexdigest()
        att_data = dict(att_data)

        is_duplicate_record = self.is_duplicate(att_hash)

        if bool(is_duplicate_record):
            return self.get_err_object("Conflict:Duplicate Entry", att_data, 409)

        if bool(att_data):

            result = None
            try:
                datetime.strptime(att_data["check_time"], "%Y-%m-%d %H:%M:%S")

                self.attendance_date, self.attendance_time = str(att_data["check_time"]).split(" ")
                self.attendance_datetime = att_data["check_time"]

                prev_date = datetime.strptime(self.attendance_date, "%Y-%m-%d") - timedelta(days=1)
                self.prev_date = datetime.strftime(prev_date, "%Y-%m-%d")

            except :
                return self.get_err_object("Bad Request:Date format is not correct.", att_data, 400)

            employee = frappe.get_all("Employee", {"name" : self.emp_id}, "name")

            if (len(employee) == 0):
                return self.get_err_object("Bad Request:Employee code not found.", att_data, 400)

            else:

                emp_shift = get_employee_shift(self.emp_id, self.attendance_date)
                emp_shift_prev = get_employee_shift(self.emp_id, self.prev_date)

                emp_att_result = frappe.db.get_all("Attendance", {
                    "attendance_date" : ("in" , (self.attendance_date, self.prev_date)),
                    "employee" : self.emp_id,
                    "docstatus" : 1,
                    }, "*")

                indexed_list = dict()
                for amp_att in emp_att_result:
                    indexed_list[datetime.strftime(amp_att["attendance_date"], "%Y-%m-%d")] = amp_att

                today_shift_start, today_shift_end = self.get_shift_start_end(self.attendance_date, emp_shift)
                
                prev_shift_start, prev_shift_end = self.get_shift_start_end(self.prev_date, emp_shift_prev)

                # check if todays checkin exists
                if str(self.attendance_date) in indexed_list:
                    result = self.current_attendance(indexed_list, today_shift_start, today_shift_end, prev_shift_end)
                
                elif str(self.prev_date) in indexed_list:
                    result = self.prev_attendance(indexed_list, prev_shift_start, prev_shift_end, emp_shift, today_shift_start)
                
                else:
                    result = self.new_attendance(today_shift_start, prev_shift_start, prev_shift_end, emp_shift_prev, emp_shift)
    
            if "error" in result:
                return self.get_err_object(result["error"], att_data, 500)
           
            else:
                self.log_attendance(att_hash, json.dumps(att_data))

                return {
                    "data_id" : att_data["id"],
                    "name" : self.emp_id,
                    "code" : 200,
                    "list_item" : result
                }


    def __del__(self):
        pass