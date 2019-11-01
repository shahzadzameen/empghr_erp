# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import sys
import string
import json, ast
import math
import datetime
from dateutil.relativedelta import relativedelta

from empg_erp.utils import (get_config_by_name, get_employee_code, get_prioritized_role, get_employee_holidays, get_time_diff, getPenaltyDateRange)

import frappe
from erpnext.hr.utils import find_substr
from frappe import _, _dict
from frappe.utils import (flt, cstr, getdate, get_first_day, get_last_day,
                          add_months, add_days, formatdate)
from collections import defaultdict

from empg_erp.modules.mustang.shift import (get_employee_shift, get_employee_shift_working_hours)
from empg_erp.constants.globals import MONTHLY_ATTENDANCE_DATE,ADMINISTRATOR, LINE_MANAGER_GUIDES
from empg_erp.modules.mustang.employee_penalty.attendance_policies import AttendancePolicies


def get_widget_data(widget, _filter = None, args=None):
    if "table" in widget["type"]:
        return get_table_widget_data(widget)
    elif "tab" in widget["type"]:
        return get_tab_widget_data(widget)
    elif "chart" in widget["type"]:
        return get_chart_widget_data(widget)
    elif "plane" in widget["type"]:
        return get_plane_widget_data(widget, _filter)


def get_table_widget_data(widget, args=None):
    conditions = get_conditions(args)
    report = get_table_report(widget["name"])
    query = get_report_query(report)
    # REPLACE WITH BOOKMARK AND GENERATE NEW QUERY
    bookmark_result = get_bookmarks(report)
    replace_result = replace_bookmark(bookmark_result, query)
    widget_data = get_data(replace_result['new_query'], conditions)
    prepare_data_for_widget(widget_data, widget)
    return widget


def get_tab_widget_data(widget, args=None):
    widget_data = {"data": [], "columns": []}
    conditions = get_conditions(args)
    tabs = get_tabs(widget["name"])
    for tab in tabs:
        tab_data = {"id": tab["name"], "title": tab["title"], "data": [], "columns": []}
        query = get_report_query(tab["report"])
        # REPLACE WITH BOOKMARK AND GENERATE NEW QUERY
        bookmark_result = get_bookmarks(tab["report"])
        replace_result = replace_bookmark(bookmark_result, query)
        # REPLACE WITH BOOKMARK AND GENERATE NEW QUERY
        result = get_data(replace_result['new_query'], conditions)
        for data in result["data"]:
            tab_data["data"].append(data)

        tab_data["columns"].extend(result["columns"])
        widget_data["data"].append(tab_data)
    prepare_data_for_widget(widget_data, widget)
    return widget


def get_chart_widget_data(widget, args=None):
    conditions = get_conditions(args)
    report = get_table_report(widget["name"])
    query = get_report_query(report)
    widget_data = get_chart_data(query, conditions)
    prepare_data_for_widget(widget_data, widget)
    return widget


def get_report_query(report, skip = True):
    query = frappe.db.sql("""
		select `query`
		from `tabWidget Report` 
		where name=%s""", report, as_list=1)[0][0]

    return find_substr("@FILTER_ST@", "@FILTER_END@", skip)(query)


def get_data(query, conditions):
    data = [list(t) for t in frappe.db.sql(query)]
    columns = [c[0] for c in frappe.db.get_description()]
    return {
        "data": data,
        "columns": columns
    }


def get_chart_data(query, conditions):
    data = frappe.db.sql(query, as_dict=1)
    data = sum_dict_value_by_key(data, 'label', 'data')
    columns = [c[0] for c in frappe.db.get_description()]
    return {
        "data": data,
        "columns": columns
    }


def sum_dict_value_by_key(data, key_field, value_field):
    dd = defaultdict(int)
    for d in data:
        dd[d[key_field]] += flt(d[value_field])
    return [{key_field: k, value_field: [[0, v]]} for k, v in dd.items()]


def get_conditions(args):
    pass


def get_table_report(widget_name):
    return frappe.db.sql("""
		select report
		from `tabWidget` 
		where name=%s order by display_order asc""", widget_name, as_list=1)[0][0]


def get_tabs(widget_name):
    return frappe.db.sql("""
		select name, tab_name as title, report
		from `tabWidget Tab` 
		where parent=%s""", widget_name, as_dict=1)


def prepare_data_for_widget(data, widget):
    widget.setdefault("data", data["data"])
    widget.setdefault("columns", data["columns"])


# WRITE FUNCTION TO ADD THE BOOKMARK

def test_plane_widget(widget):
    bm = frappe.get_doc({"doctype" : "Bookmark"})
    wd = frappe.get_doc({"doctype" : "Widget"})
    widget_row = bm.get_widget(widget["name"])
    # widget_report = get_report_query(widget_row.report)
    bookmark_result = bm.get_bookmarks(widget_row.report)
    replace_result = bm.evaluate_bookmarks(bookmark_result, widget_row.query)
    widget_data = bm.get_plane_data(replace_result)

    wd.eval_template_function(**{
        "template": widget_row.template, 
        "widget_data": widget_data, "widget_title" : widget_row.title, 
        "heading" : widget_row.heading, "redirect_url" : widget_row.redirect_url,
        "background_color" : widget_row.background_color
        })
    widget["data"] = {
        "template" : wd.template,
        "widget_type" : wd.widget_type,
        "widget_title" : widget_row.title
    }

def get_plane_widget_data(widget, _filter = None, args=None):
    report = get_plane_report(widget["name"])
    query = get_report_query(
        report['report'], 
        (True if _filter == "All" else False)
        )

    # REPLACE WITH BOOKMARK AND GENERATE NEW QUERY
    bookmark_result = get_bookmarks(report['report'])
    replace_result = replace_bookmark(bookmark_result, query)

    widget_data = get_plane_data(replace_result['new_query'], replace_result['template'])
    widget_template = widget_data['template']
    # REPLACE BOOKMARKS WHICH IS USED IN HTML TEMPLATE
    result = get_data_and_bookmark(widget_template, widget_data)
    widget_type = result['widget_type']
    widget_data_rows = result['widget_data_rows']
    bookmark = result['bookmark']
    widget_data = result['widget_data']

    # REPLACE INNER BOX BOOKMARKS WHICH IS USED IN HTML TEMPLATE
    widget_template = replace_inner_html_bookmark(widget_template, widget_data_rows, bookmark)
    # REPLACE BOOKMARKS FROM THE HTML TEMPLATE
    if (widget_type != 'rightSide'):
        widget_template = replace_bookmark_from_template(widget_template, widget_data_rows, bookmark, widget_data)
    widget_data['template'] = widget_template
    widget_data['widget_type'] = widget_type
    widget_data['widget_title'] = report['title']
    prepare_data_for_plane_widget(widget_data, widget)
    return widget



# check the condition and get the bookmark
def get_data_and_bookmark(widget_template, widget_data):
    # REPLACE BOOKMARKS WHICH IS USED IN HTML TEMPLATE
    bookmark = widget_type = ''
    if (widget_template.find('@LeaveInnerBoxBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "LeaveInnerBoxBookmark"
    elif (widget_template.find('@RewardInnerBoxBookmark@') != -1):
        working_hours = get_employee_shift_working_hours(get_employee_code())  # Calculate working hours
        reward = widget_data['data'][0]['reward']
        reward_conversion = convert_reward(reward, int(working_hours))  # Convert Reward
        widgets = {'data': {}}
        year = datetime.datetime.now().year  # Current Year
        widgets['data'][0] = reward_conversion
        widget_data['data'][0] = reward_conversion
        widget_data['data'][0]['year'] = year
        widget_data_rows = sorted(widgets['data'][0].keys())
        bookmark = "RewardInnerBoxBookmark"
    elif (widget_template.find('@PenaltyInnerBoxBookmark@') != -1):
        result = render_penalty_widget_data()
        widget_data_rows = {}
        widget_data_rows['minutes'] = result['minutes']
        widget_data_rows['instances'] = result['instances']
        widget_data['data'][0] = result
        bookmark = "PenaltyInnerBoxBookmark"
    elif (widget_template.find('@MyHolidayCalendarBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "MyHolidayCalendarBookmark"
        widget_type = 'rightSide'
    elif (widget_template.find('@BirthdayBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "BirthdayBookmark"
        widget_type = 'rightSide'
    elif (widget_template.find('@AnnouncementsBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "AnnouncementsBookmark"
        widget_type = 'rightSide'
    elif (widget_template.find('@DailyShiftBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "DailyShiftBookmark"
    elif (widget_template.find('@ColumnInnerBoxBookmark@') != -1):
        widget_data_rows = widget_data['data'][0].keys()
        bookmark = "ColumnInnerBoxBookmark"
    elif (widget_template.find('@EmpMonthlyTurnoverData@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "EmpMonthlyTurnoverData"
    elif (widget_template.find('@PieChartBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "PieChartBookmark"
    elif (widget_template.find('@TaskListBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "TaskListBookmark"
    elif (widget_template.find('@TeamHolidayAndLeave@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "TeamHolidayAndLeave"
    elif (widget_template.find('@AnnualLeaveBookmark@') != -1):
        widget_data_rows = widget_data['data']
        bookmark = "AnnualLeaveBookmark"
    else:
        if (widget_template.find('@profile_score@') != -1):
            if len(widget_data['data']) == 0:
                if ADMINISTRATOR in frappe.get_roles():
                    widget_data['data'].append({'profile_score': 0, 'employee_name': '#List/Employee/List'})
                else:
                    widget_data['data'].append({'profile_score': 0, 'employee_name': '#Form/Employee/{0}'.format(get_employee_code())})
            else:
                widget_data['data'][0]['employee_name'] = '#Form/Employee/{0}'.format(get_employee_code())
        if len(widget_data['data']) == 0:
            widget_data['data'].append({'sum': 0})
        widget_data_rows = widget_data['data'][0].keys()

    return {'widget_data_rows': widget_data_rows, 'bookmark': bookmark, 'widget_type': widget_type,
            'widget_data': widget_data}


def get_plane_report(widget_name):
    return frappe.db.sql("""
		select report, title
		from `tabWidget` 
		where name=%s order by display_order asc""", widget_name, as_dict=True)[0]


def get_plane_data(query, template):
    queryChunks = query.strip().split("|||||")
    _qChunks = queryChunks[:-1]
    for queryChunk in _qChunks:
        frappe.db.sql(queryChunk)

    frappe.db.commit()
    data = frappe.db.sql(queryChunks[-1], as_dict=True)
    return {
        "data": data,
        "template": template,
        "type": "custom_template",
        "widget_type": "",
        "widget_title": ""
    }


# PREPARE DATA FOR PLANE WIDGET
def prepare_data_for_plane_widget(data, widget):
    widget.setdefault("data", data)


# widget.setdefault("columns", data["columns"])

# GET BOOKMARKS BY WIDGET NAME
def get_bookmarks(widget_name):
    return frappe.db.sql("""
		SELECT title,type,value FROM tabBookmark where widget_report = '{0}'""".format(widget_name), as_dict=True)


# REPLACE BOOKMARK IN QUERY
def replace_bookmark(results, query):
    bookmark = new_query = template = ""
    if new_query == "":
        new_query = query

    for result in results:
        if result["type"] != "Template":
            if "Constant" in result["type"]:
                bookmark = """'{0}'""".format(eval(result["value"]))
            elif "Function" in result["type"]:
                execute = eval(result["value"])
                if not execute:
                    execute = 0
                bookmark = """'{0}'""".format(execute)
            elif "Query" in result["type"]:
                bookmark = """{0}""".format(eval(result["value"]))
            new_query = string.replace(new_query, """@{0}@""".format(result["title"]), bookmark)
        elif "Template" in result["type"]:
            template = result["value"]
    return {'new_query': new_query, 'template': template}


def replace_bookmark_from_template(widget_template, widget_data_rows, bookmark, widget_data):
    total = 0

    if bookmark == "PenaltyInnerBoxBookmark":
        widget_data_rows['total'] = widget_data['data'][0]['total']
        widget_data_rows['title'] = widget_data['data'][0]['title']

    for data in widget_data_rows:
        if bookmark == "LeaveInnerBoxBookmark":
            total += data.total
        elif bookmark in ["DailyShiftBookmark", "PieChartBookmark", "EmpMonthlyTurnoverData",
                          "TeamHolidayAndLeave", "TaskListBookmark", "AnnualLeaveBookmark"]:
            widget_template = widget_template
        else:
            widget_template = string.replace(widget_template, """@{0}@""".format(data),
                                             """{0}""".format(widget_data['data'][0][data]))

    if widget_template.find('@sum@') != -1:
        widget_template = string.replace(widget_template, """@{0}@""".format('sum'),
                                         """{0}""".format(total))
    return widget_template


# Dynamic InnerBox and CALENDAR Code widgets
def replace_inner_html_bookmark(widget_template, widget_data_row, bookmark):
    if bookmark == "MyHolidayCalendarBookmark":
        html = holiday_calendar_html(widget_data_row)
    elif bookmark == "DailyShiftBookmark":
        html = daily_shift_calendar_json(widget_data_row)
    elif bookmark == "EmpMonthlyTurnoverData":
        html = emp_monthly_turnover_barchart_json(widget_data_row)
    elif bookmark == "PieChartBookmark":
        html = piechart_json(widget_data_row)
    elif bookmark == "TaskListBookmark":
        html = task_list(widget_data_row)
    elif bookmark == "TeamHolidayAndLeave":
        html = holiday_and_leave_barchart_json(widget_data_row)
    elif bookmark == "BirthdayBookmark":
        html = birthday_wishes_html(widget_data_row)
    elif bookmark == "AnnouncementsBookmark":
        html = announcements_html(widget_data_row)
    elif bookmark == "AnnualLeaveBookmark":
        html = annual_leaves_html(widget_data_row)
    else:
        html = inner_box_html(widget_data_row, bookmark)
    new_widget_template = string.replace(widget_template, """@{0}@""".format(bookmark), """{0}""".format(html))
    return new_widget_template


# Widget Small BOX html RENDERED
def inner_box_html(widget_data_row, bookmark):
    html = '<div class="row">'
    for data in widget_data_row:
        if bookmark == "LeaveInnerBoxBookmark":
            title = data.leave_type
            value = str(data.total)
        else:
            title = data.title()
            value = '@' + data.lower() + '@'
        if data != "total" and data != "year":  # ignore total and year bookmark
            html += '<div class="dashboard-widget-box-inner"><span class="font-weight-bold box_count">' + value + '</span>' + title + '</div>'
    html += '</div>'
    return html


# Holiday Calendar li html rendered
def holiday_calendar_html(widget_data_row):
    html = ''
    if widget_data_row is not None and len(widget_data_row) > 0:
        for data in widget_data_row:
            if data.holiday_date is not None:
                if data.type == "visa_expiry":
                    description = data.description
                    if len(description) > 22:
                        description = description[:21] + '...'
                    html += "<li title ='" + str(
                        data.description) + "' class='font-weight-bold text-uppercase' title= '"+data.description+"'>" + description+ '<span class="pull-right">' + str(
                    datetime.datetime.strftime(data.holiday_date, '%d, %b')) + '</span>' + "</li>"
                else:
                    holiday_date = frappe.utils.formatdate(data.holiday_date)
                    html += '<li title="' + str(data.description) + '">' + str(data.description) + ' (' + str(
                        holiday_date) + ')</li>'
            else:
                html = "<p class='no-holiday text-center'>No Record found yet</p>"
    else:
        html = "<p class='no-holiday text-center'>No Record found yet</p>"
    return html


# Birthday wishes html rendered
def birthday_wishes_html(widget_data_row):
    html = date_right = ''
    flag = 0
    if widget_data_row is not None and len(widget_data_row) > 0:
        for data in widget_data_row:
            fullname = str(data.fullname)
            if flag == 0 and data.type == 'birthday':
                html += '<p><i class="fa fa-birthday-cake fa-3x"></i></p>'
                html += "<p class='text-uppercase'>" + str(
                    datetime.datetime.strftime(datetime.datetime.today(), '%d, %B')) + "</p>"
            if data.type == 'upcoming':
                date_right = '<span class="pull-right">' + str(
                    datetime.datetime.strftime(data.date, '%d, %b')) + '</span>'
                if len(fullname) > 16:
                    fullname = fullname[:16] + '...'
            html += "<li title ='" + str(
                data.fullname) + "' class='font-weight-bold text-uppercase'>" + fullname + date_right + "</li>"
            flag = flag + 1
    else:
        html = "<p class='no-holiday text-center'>No Record found yet</p>"
    return html


# Daily shift Calendar EVENT JSON
def daily_shift_calendar_json(widget_data_row):
    daily_dict = []
    for data in widget_data_row:
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

    return ast.literal_eval(json.dumps(daily_dict))


def emp_monthly_turnover_barchart_json(widget_data_row):
    turnover_data = []
    if frappe.session.user == ADMINISTRATOR:
        employee_name = 'Administrator'
    else:
        employee_name = frappe.db.get_value('Employee', {'user_id': frappe.session.user}, 'employee_name')
        for _data in widget_data_row:
            turnover_data.append(_data['turnover'])

    data = [
        {
            "name": employee_name,
            "data": turnover_data
        }
    ]

    return ast.literal_eval(json.dumps(data))

def piechart_json(widget_data_row):
    return ast.literal_eval(json.dumps(widget_data_row))

def task_list(widget_data_row):
    if widget_data_row is not None and len(widget_data_row) > 0:
        html = ""
        for data in widget_data_row:
            if data.description != "":
                html += "<li>{0}<li>".format(data.description)
    else:
        html = "<p class='no-holiday text-center'>You're up to date!</p>"
    return html

def holiday_and_leave_barchart_json(widget_data_row):
    data = []
    for _data in widget_data_row:
        _tmp_dict = {}
        _tmp_dict["name"] = _data["leave_type"]
        _tmp_dict["data"] = map(int, _data["leave_counts"].split(','))
        data.append((_tmp_dict))
    return ast.literal_eval(json.dumps(data))


def annual_leaves_html(widget_data_row):
    html = '<div class="">'
    if widget_data_row is not None and len(widget_data_row) > 0:
        for data in widget_data_row:
            html += '<div class="font-size-12 line-height-widget"><span class="text-left">' + str(data.name) + '</span><span class="font-weight-bold pull-right font-size-12">' + str(data.total) + '</span></div>'
        html += '</div>'
    else:
        html = "<p class='no-holiday text-center m-0'>No Record found yet</p>"
    return html

# Convert reward with minutes, working hours
def convert_reward(minutes, shiftHours):
    return {
        'days': int(math.floor(minutes / (60 * shiftHours))),
        'hours': int(math.floor((minutes / 60) % shiftHours)),
        'minutes': int(minutes % 60)
    }


# Announcement li html rendered
def announcements_html(widget_data_row):
    html = ''
    if len(widget_data_row) > 0:
        for data in widget_data_row:
            date = frappe.utils.formatdate(data.date)
            description = data.title
            url = str(data.document)
            truncate_description = description
            if len(description) > 25:
                truncate_description = description[:25] + '...'
            if data.type != "guides":
                url = "#Form/Announcement/" + description
            html += '<li title="' + description + '"><a href= "'+url+'" target="_blank" class="no-hover-underline">' + truncate_description + ' <span class="display-block font-weight-normal">' + str(
                date) + '</span></a> ' \
                        '<a href= "#Form/Announcement/' + description + '" target="_blank" class="announcment-paperclip"><i class="fa fa-paperclip"></i></a></li>'

    else:
        html = "<p class='no-holiday text-center'>No Record found yet</p>"
    return html

# Calculate the Penalty Widgets
def calculate_penalty_widgets():
    result = {}
    userid = get_employee_code()
    date = datetime.datetime.today().strftime('%Y-%m-%d')
    now = datetime.datetime.now()
    if (now.day > MONTHLY_ATTENDANCE_DATE):
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


# render the final penalty widget data
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

    return {'minutes': total_late_arrival, 'instances': total_late_instance, 'title': title, 'total': count}