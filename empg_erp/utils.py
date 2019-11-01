import frappe
from frappe import get_meta, get_doc
import time
from frappe.utils import get_site_base_path,get_url_to_list,get_url_to_form
from os import getenv, path
import math
import calendar
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json
from .empg_erp.doctype.allotted_advance_privileges.allotted_advance_privileges import get_advance_privileges
from .constants.globals import SITE_MODULES_PATH,PAGE_SIZE,LINE_MANAGER,HR_USER,HR_MANAGER,ADMINISTRATOR,EMPLOYEE,ATTENDANCE_MANAGER, \
    MONTHLY_ATTENDANCE_DATE,ROSTER_STATUS_OFF,ATTENDANCE_STATUS_PRESENT,SYSTEM_MANAGER, STATUS_OPEN,STATUS_APPROVED,STATUS_REJECTED
from six import string_types
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


@frappe.whitelist()
def custom_set_property(docType, field_name, docPropertyName="in_list_view", docPropertyValue=0, docPropertyType="Check"):
    make_property_setter(docType, field_name, docPropertyName, docPropertyValue, docPropertyType)


@frappe.whitelist(allow_guest=True)
def get_site_config():
    _config = frappe.cache().hget("site_configurations", "config")
    if not _config:
        _config = cache_site_config()
    return _config

def cache_site_config():
    from erpnext.setup.doctype.site_configuration.site_configuration import SiteConfiguration
    _config = SiteConfiguration.update_cache()
    return _config

def get_config_by_name(name, default = None):
    _config = get_site_config()
    if name in _config:
        return _config[name]

    return default

def get_site_path():

    return getenv('ENVIRONMENT', 'mustang')

    # _site_dir = SITE_MODULES_PATH.values()[0]

    # for key, site_dir in SITE_MODULES_PATH.iteritems():

    #     env_variable = getenv(key, None)

    #     if(get_site_base_path()[2:] == env_variable):
    #         _site_dir = SITE_MODULES_PATH[key]
    #         break
    
    # return _site_dir

def import_attr(module_name, attr, default = None):
    try:
        common_attr = getattr(__import__("empg_erp.modules.common.hooks", fromlist=[attr]), attr, default)
        site_attr   = getattr(__import__(module_name, fromlist=[attr]), attr, default)

        if(isinstance(site_attr, list) and isinstance(common_attr, list)):
            return site_attr + common_attr
        elif(isinstance(site_attr, dict) and isinstance(common_attr, dict)):
            return dict(site_attr.items() + common_attr.items())
        else:
            return site_attr
    except:
        return default

def get_limit_from_filters(filters, per_page = 20):
    
    page = 0
    if "page" in filters:
        page = filters["page"]
    
    return get_limit(page, per_page)

def get_page_count(count, per_page = 20):

    return (math.ceil(count/per_page)-1)

def get_limit(page, per_page = 20):

    return per_page, (int(page) * per_page)


def path_child(query, parent_data, key, child_key):

    ids = list()
    
    for data in parent_data:
        if key in data:
            ids.append(data[key])
            
    query = query.format("'"+"','".join(ids) + "'")
    
    child_data = frappe.db.sql(query, as_dict=True)
    
    indexed_data = dict()
    
    for child in child_data:
        if key in child:
            indexed_data[child[key]] = child
            
    for index, value in enumerate(parent_data):
        if value[key] in indexed_data:
                parent_data[index][child_key] = indexed_data[value[key]]
    
    return parent_data

def get_timestamp(date_time):

    try :
        if(isinstance(date_time, str) or isinstance(date_time, unicode)):
            return calendar.timegm(datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").utctimetuple()) 
        else:
            return calendar.timegm(date_time.utctimetuple())
    except :
        return 0

def get_time_diff(start_time, end_time, type = "secs"):

    _divider = 1

    if type == "mins":
        _divider = 60

    if type == "hours":
        _divider = 3600

    if type == "days":
        _divider = 216000

    
    return round( float( get_timestamp(start_time) - get_timestamp(end_time) ) / _divider, 2 )

def unlock_doc(doc_type, doc_id):

    try:
        frappe.db.sql("""
            UPDATE `tab{0}` a
            SET docstatus = 0
            WHERE a.name = "{1}"
        """.format(doc_type, doc_id))
    except Exception as err:
        return err

def unlock_doc_list(doc_type, docs = []):
    
    _sql = """
        UPDATE `tab{0}` a
        SET docstatus = 0
        WHERE a.name IN ({1})
    """.format(
        doc_type, 
        "'" + "','".join(docs) + "'"
        )
    try:
        frappe.db.sql(_sql)
    except Exception as err:
        return err
        
@frappe.whitelist()
def get_employee_code():
	return frappe.db.get_value('Employee', {'user_id': frappe.session.user}, 'name')

@frappe.whitelist()
def get_months_and_year(getTillLastYear = 12):
	now = time.localtime()
	months = [time.localtime(time.mktime((now.tm_year, (now.tm_mon)  - n, 1, 0, 0, 0, 0, 0, 0)))[:2] for n in range(getTillLastYear)]
	months_name = []

	for month in months:
		row = []
		row.append(date(1900, month[1], 1).strftime('%b'))
		row.append((month[0]))
		months_name.append(row)


	return months_name

def get_employee_holidays(employee_code):
    return frappe.db.sql("""
    SELECT
    IF(hl.name IS NOT NULL,
        h.holiday_date,
        ch.holiday_date) AS holiday_date,
    IF(hl.name IS NOT NULL,
        h.description,
        ch.description) AS description
    FROM
        tabEmployee e
            LEFT JOIN
        `tabHoliday List` hl ON hl.name = e.holiday_list
            LEFT JOIN
        `tabHoliday` h ON h.parent = hl.name
            LEFT JOIN
        `tabCompany` c ON c.name = e.company
            LEFT JOIN
        `tabHoliday List` chl ON chl.name = c.default_holiday_list
            LEFT JOIN
        `tabHoliday` ch ON ch.parent = chl.name
    WHERE
        e.name = '{0}'
    GROUP BY holiday_date;
    """.format(employee_code), as_dict= 1)

def get_table_name(name):
    return "tab{0}".format(name)


def str_to_date(date, format='%Y-%m-%d'):
    if(isinstance(date, string_types)):
        return datetime.strptime(date, format)
    return datetime.strptime(date.strftime(format), format)
 
def get_monthly_diff_dates(day = None, months = 1, month = None):

    start_date = datetime.today()
    start_month = start_date.month

    if day == None:
        day = int(datetime.strftime(start_date, "%d"))

    if month != None:
        start_month = (month % 12)

    edge_day = calendar.monthrange(start_date.year, start_month)[1]
    if (day > edge_day):
        day = edge_day

    try :

        date_end = datetime(start_date.year, start_month, day)
        end_date = date_end - relativedelta(months=months)

        date_end = datetime.strftime(date_end, "%Y-%m-%d")
        
        edge_day = calendar.monthrange(end_date.year, end_date.month)[1]
        if (day > edge_day):
            day = edge_day
        
        date_start = datetime(end_date.year, end_date.month, day)
        date_start = datetime.strftime(date_start, "%Y-%m-%d")

        return date_start, date_end
    except Exception as err:
        return str(err)

def get_user_advance_privileges():
    employee_code = get_employee_code()
    advance_privs = []
    if(employee_code):
        advance_privs = frappe.cache().hget("advance_privileges", get_employee_code()) or None
        if advance_privs:
            return advance_privs
        advance_privs = get_advance_privileges()
        if advance_privs:
            frappe.cache().hset('advance_privileges', get_employee_code(), advance_privs)
    return advance_privs

@frappe.whitelist()
def check_advance_privilege_by_name(name=None):
    if(frappe.session.user == ADMINISTRATOR):
        return True
    if(name):
        _privs = get_user_advance_privileges()
        if name in _privs:
            return True
    return False

@frappe.whitelist()
def get_user_role(user_id = None ):
    user = None
    if user_id == None:
        user_id = frappe.session.user
        
    AuthRole = frappe.get_roles(user_id)

    # check if it is administrator
    if ADMINISTRATOR in AuthRole:
        user = ADMINISTRATOR
    else:
    #if it is an employee Hr or Employee LineManager
        if EMPLOYEE in AuthRole:
           if HR_MANAGER not in AuthRole:
               #check if it exists as reports to
               employee = frappe.db.get_value("Employee", {"user_id": user_id}, "employee")
               reports_to = frappe.db.get_value("Employee", {"reports_to": employee}, "reports_to")
               if reports_to is not None:
                  user = LINE_MANAGER
               else:
                  user = EMPLOYEE
           else:
               user = HR_MANAGER

    return user

@frappe.whitelist()
def get_report_to(name,email=False):
    _reports_to = frappe.db.get_value("Employee", {"name": name}, "reports_to")
    if email==False:
        return _reports_to
    else:
        return frappe.db.get_value("Employee", {"name": _reports_to}, "user_id")  
     
        
def get_auth_team_ids(returnList = False):
    employee_list = frappe.get_list("Employee", {}, ["name"])

    if returnList == True:
        team_Ids = []
        for emp_id in employee_list:
            team_Ids.append(emp_id.get("name"))
    else:
        team_Ids = ""
        i = 0
        for emp_id in employee_list:
            if (i == len(employee_list) - 1):
                team_Ids += '\''+(emp_id.get("name")) +'\''
            else:
                team_Ids += '\''+(emp_id.get("name"))+'\'' + ","

            i+=1


    return team_Ids

def get_user_filters_by_role():

    filter_list = ["Me"]
    default_user_filter = "Me"

    user = get_user_role()
    # TODO: Make it handle by HR user Role form get_user_role
    if HR_USER in frappe.get_roles(frappe.session.user):
        filter_list = ["Employee Reporting To Me", "Me", "All Team"]
        default_user_filter = "All Team"
    elif user == EMPLOYEE:
       filter_list = ["Me"]
       default_user_filter = "Me"
    elif user == HR_MANAGER:
        filter_list = ["Employee Reporting To Me", "Me", "All Team"]
        default_user_filter = "All Team"
    elif user == LINE_MANAGER:

        filter_list = ["Employee Reporting To Me", "Me", "All Team"]
        default_user_filter = "Me"
    elif user == ADMINISTRATOR:
        filter_list = []
        default_user_filter = ""

    if ATTENDANCE_MANAGER in frappe.get_roles(frappe.session.user):
        filter_list = ["Employee Reporting To Me", "Me", "All Team"]
        default_user_filter = "All Team"

    return filter_list,default_user_filter

def getPenaltyDateRange(date):
    # start of month
    date = datetime.strptime(str(date), '%Y-%m-%d')
    start_of_month = date.strftime('%Y-%m-01')
    start_of_month = datetime.strptime(start_of_month, '%Y-%m-%d')
    # end date for month suppose(2018 - 08-27 changed to 2018-08-20) according to config
    month_end_date = start_of_month.strftime('%Y-%m-' + str(MONTHLY_ATTENDANCE_DATE))
    # start date for month suppose(2018 - 08-20 changed to 2018-07-20) according to config
    month_start_date = datetime.strptime(month_end_date, '%Y-%m-%d') - relativedelta(months=1)
    month_start_date = month_start_date.strftime('%Y-%m-' + str(int(MONTHLY_ATTENDANCE_DATE)+1))
    return {'month_start_date': month_start_date, 'month_end_date': month_end_date}

def get_date_diff_in_days(date1,date2):
    delta = date2 - date1
    return delta.days

# TODO
# Make this function compatible with configurable start day of week
def get_start_end_date_of_last_week():
	today = datetime.today()
	start_day_date = today + timedelta(days=-today.weekday()-7, weeks=0)
	end_day_date = start_day_date + timedelta(days=-1, weeks=1)
	start_day_date = datetime.strftime(start_day_date, "%Y-%m-%d")
	end_day_date = datetime.strftime(end_day_date, "%Y-%m-%d")
	return start_day_date, end_day_date


def get_post_body():
   
    data = {}

    try:
        _dict_body_keys = frappe.request.form.to_dict().keys()
        _dict_body_values = frappe.request.form.to_dict().values()

        if len(_dict_body_keys) > 0:
            data = _dict_body_keys[0]
        elif len(_dict_body_values) > 0:
            data = _dict_body_values[0]
        else:
            return data
        
        return json.loads(data)

    except Exception as err:
        print(err)
        return None

def get_desktop_icons_list(site_dir):
    desktop_list = {
        "mustang": ["HR", "Employee", "Widgets", "Leave Application", "Announcement", "Policy Document Category",
               "Daily Attendance Report", "Late Attendance Report", "Absent Report", "Employee Leave Balance",
               "Attendance Request"],
        "explorer": ["HR", "Employee", "Expense Claim", "Widgets", "Leave Application", "Announcement", "Company Documents", "Appraisal",
                     "e-HR Employees", "Letter Request", "Refer a Friend", "Employee Leave Balance"]
    }
    return desktop_list[site_dir]

def custom_query_report_icons(site_dir):
    desktop_list = {
        "mustang": ["Late Attendance Report", "Absent Report", "Daily Attendance Report", "Employee Leave Balance"],
        "explorer": ["Company Documents", "Employee Leave Balance"]
    }
    return desktop_list[site_dir]


def get_formatted_hours(hrs):

    formatted_hours = str(timedelta(hours=float(hrs)))
    formatted_hours = formatted_hours.split(':')
    formatted_hours = formatted_hours[0] + 'hr ' + formatted_hours[1] + 'm'
    if "days" in formatted_hours:
        formatted_hours = formatted_hours.split(',')
        formatted_hours = formatted_hours[1]

    return formatted_hours

def get_employee_shift_timings(employee):
    _df_start_time = get_config_by_name("default_shift_start_time", "09:00:00")
    _df_end_time = get_config_by_name("default_shift_end_time", "18:00:00")

    return frappe.db.sql("""SELECT 
        time_format(IF(st.start_time IS NULL,%(start_time)s,st.start_time), %(time_format)s) AS start_time,
        time_format(IF(st.end_time IS NULL,%(end_time)s,st.end_time), %(time_format)s) AS end_time
    FROM
        `tabEmployee` emp
    LEFT JOIN
        `tabShift Type` st ON st.name = emp.shift_type
    WHERE
        emp.name = %(employee)s """,({
            "start_time" : _df_start_time,
            "end_time" : _df_end_time,
            "employee" : employee,
            "time_format" : "%H:%i:%s"
        }), as_dict= 1)[0]



def get_date_range(start_day, end_day, month = None, months = 1):
    
    start_date = datetime.today()
    start_month = start_date.month

    if month != None:
        start_month = (month % 12)

    edge_day = calendar.monthrange(start_date.year, start_month)[1]
    if (end_day > edge_day):
        end_day = edge_day

    try :

        date_end = datetime(start_date.year, start_month, end_day)
        end_date = date_end - relativedelta(months=months)

        date_end = datetime.strftime(date_end, "%Y-%m-%d")
        
        edge_day = calendar.monthrange(end_date.year, end_date.month)[1]
        if (start_day > edge_day):
            start_day = edge_day
        
        date_start = datetime(end_date.year, end_date.month, start_day)
        date_start = datetime.strftime(date_start, "%Y-%m-%d")

        return date_start, date_end
    except Exception as err:
        frappe.log_error(err)
        return str(err)

def get_previous_version(doctype, name):
   
	meta  = get_meta(doctype)
	if meta.track_changes:
		docs = frappe.db.sql("""
			SELECT name, data from tabVersion
			WHERE  ref_doctype = '{doctype}' AND docname = '{name}'
			ORDER BY creation DESC
			LIMIT 1
		""".format(
			doctype  = doctype,
			name     = name,
		), as_dict=True)

		from frappe.chat.util import safe_json_loads

		version = None

        if len(docs) > 0:
			version = docs[0].data
			version = safe_json_loads(version)
            
        return version


def copy_fields(copy_to, copy_from, fields = []):

    for field in fields:
        if field in copy_from.__dict__ and field in copy_to.__dict__:
            copy_to.__dict__[field] = copy_from.__dict__[field]

def get_month_day_range(date):
    """
    For a date 'date' returns the start and end date for the month of 'date'.

    Month with 31 days:
    >>> date = datetime.date(2011, 7, 27)
    >>> get_month_day_range(date)
    (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

    Month with 28 days:
    >>> date = datetime.date(2011, 2, 15)
    >>> get_month_day_range(date)
    (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
    """
    first_day = date.replace(day = 1)
    last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day

@frappe.whitelist(allow_guest=True)
def check_doctype_restriction():
    restricted_docs = []
    employee = get_employee_code()
    max_priority = frappe.db.sql("select max(priority) as max_priority from `tabEmployee Doctype Restriction`")
    docs = frappe.db.get_values('Employee Doctype Restriction', {'employee': employee,'status':'Open', 'priority': max_priority[0][0]}, 'document_type',as_dict=True)
    for doc in docs:
        url = get_url_to_list(doc.document_type)
        if doc.document_type == "Employee":
            url = get_url_to_form(doc.document_type,employee)
        elif doc.document_type == "Employee Verification":
            # get name of the doc
            _emp_ver_name = frappe.db.get_value("Employee Verification", {"employee": employee})
            if _emp_ver_name:
                url = get_url_to_form(doc.document_type,_emp_ver_name)
        restricted_docs.append({
            "doc":doc.document_type,
            "url":url
        })
    return restricted_docs
@frappe.whitelist()
def get_status_list(islocal,employee=None,doctype=None):
    if(islocal=="new"):
        return [STATUS_OPEN]

    if(any(x in frappe.get_roles() for x in [HR_MANAGER, HR_USER, LINE_MANAGER,ADMINISTRATOR]) and islocal != "new" ):
        if (employee is not None and employee == get_employee_code()):
            return [STATUS_OPEN]

        return [STATUS_OPEN, STATUS_APPROVED, STATUS_REJECTED]
    else:
        return [STATUS_OPEN]

@frappe.whitelist()
def get_prioritized_role():
    _role = None

    _user_roles = frappe.get_roles(frappe.session.user)
    _prioritized_roles = [SYSTEM_MANAGER, ADMINISTRATOR, HR_MANAGER, HR_USER, LINE_MANAGER, EMPLOYEE]

    _role = next(iter(filter(lambda x: x in _user_roles, _prioritized_roles)))

    return _role
