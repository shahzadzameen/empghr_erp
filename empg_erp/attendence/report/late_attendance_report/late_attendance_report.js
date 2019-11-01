// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Late Attendance Report"] = {
		"filters": [
	    {
        "fieldname": "department",
           "label": __("Select Department"),
           "fieldtype": "Link",
        "options": "Department",
        "on_change": function() {
            scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
        },
        {
        "fieldname": "user",
           "label": ("Select User"),
           "fieldtype": "Select",
           "options": "",
        "on_change": function() {
            scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},

        },
	    {
        "fieldname": "employee",
           "label": __("Select Employee"),
           "fieldtype": "Link",
        "options": "Employee",
        "on_change": function() {
            scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
        },
        {
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"on_change": function() {
			    scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today(),
			"on_change": function() {
			    scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
		},
		{
		"fieldname": "page",
		"label": __("Select Page"),
		"fieldtype": "Select",
		"options": "",
		"on_change": function() {
		    scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
	    }

    ],
    "onload": function() {
        window.pagination.hideDefaultFilter();
		return frappe.call({

			method: "empg_erp.attendence.report.late_attendance_report.late_attendance_report.getPaginationData",
			args: {filters : frappe.query_report.get_filter_values()
			 },
			callback: function(r) {

				var page_filter = frappe.query_report.get_filter('page');
				window.pagination.totalRecords = r.message.totalRecords;
				page_filter.df.options = window.pagination.paginateLimit;
		    	page_filter.refresh();
			    // page_filter.set_input();
                if(r.message.user === undefined || r.message.user.length == 0){
                        $('select[data-fieldname="user"]').parent().remove();
                }else{
                var user_filter = frappe.query_report.get_filter('user');
				user_filter.df.options = r.message.user;
		    	user_filter.refresh();
			    user_filter.set_input();
			     $('select[data-fieldname="user"]').val(r.message.default_filter);
                window.pagination.hideDefaultFilter();
                setTimeout(function(){
                    window.pagination.show_limit_paging();
                },250);
              }
			}
		});
	}
}

function getPagesCount() {
		return frappe.call({
			method: "empg_erp.attendence.report.late_attendance_report.late_attendance_report.getPaginationData",
			args: {filters : frappe.query_report.get_filter_values()
			 },
			callback: function(r) {
				var page_filter = frappe.query_report.get_filter('page');
				page_filter.df.options = window.pagination.paginateLimit;
		    	page_filter.refresh();
			    // page_filter.set_input();
                window.pagination.hideDefaultFilter();
                setTimeout(function(){
                    window.pagination.show_limit_paging();
                },250);
			}

		});

	}

get_late_arrival = function(event, id){
return frappe.call({
			method: "empg_erp.attendence.report.late_attendance_report.late_attendance_report.getPopUpData",
			args: {"employee_id": id, filters : frappe.query_report.get_filter_values()},
			callback: function(r) {
			    setTimeout(function(){
                    $('body').find('.msgprint').parent().parent().parent().parent().addClass('modal-lg');
                    $('body').find('.msgprint').parent().parent().css('overflow-x','auto');
                },200);
			   var html = "<div class='padding-right-14 width-140'><table class='table table-bordered'>"+
                          "<thead class='font-size-12 theme-tbl-color'>"+
                             "<tr>"+
                               "<th>"+__('Code')+"</th>"+
                               "<th>"+__('Employee')+"</th>"+
                               "<th>"+__('Date')+"</th>"+
                               "<th>"+__('Day')+"</th>"+
                               "<th>"+__('Shift')+"</th>"+
                               "<th>"+__('Checkin-Time')+"</th>"+
                               "<th>"+__('Checkout-Time')+"</th>"+
                               "<th>"+__('Arrived Late By(mins)')+"</th>"+
                               "<th>"+__('Left Early By(mins)')+"</th>"+
                               "<th>"+__('Working Hours')+"</th>"+
                               "<th>"+__('Leave Status')+"</th>"+
                             "<tr>"+
                          "</thead>";
                for(i = 0;  i<r.message[0].length; i++){
                    var working_hrs = (r.message[0][i].workingHrs == '-') ? r.message[0][i].workingHrs : moment.duration(parseFloat(r.message[0][i].workingHrs),'h').hours()+'hr '+moment.duration(parseFloat(r.message[0][i].workingHrs),'h').minutes()+'m';
                    html += "<tr class='font-size-12'>"+
                                  "<td>"+r.message[0][i].employeeID+"</td>"+
                                  "<td>"+r.message[0][i].EmployeeName+"</td>"+
                                  "<td>"+r.message[0][i].attendanceDate+"</td>"+
                                  "<td>"+r.message[0][i].dayName+"</td>"+
                                  "<td><div class='text-left'><span class='indicators-shift' style='background-color:"+r.message[0][i].color+"'></span>"+r.message[0][i].employee_shift+"</div></td>"+
                                  "<td>"+r.message[0][i].checkIn+"</td>"+
                                  "<td>"+r.message[0][i].checkOut+"</td>"+
                                  "<td>"+r.message[0][i].LateArrivalMinutes+"</td>"+
                                  "<td>"+r.message[0][i].leftEarly+"</td>"+
                                  "<td>"+working_hrs+"</td>"+
                                  "<td>"+r.message[0][i].LeaveStatus+"</td>"+
                             "</tr>";
                }
               html += "</table></div>";

				frappe.msgprint(html, __('Late Arrival Details'));

			}

		});
}

function scrollTop(){
    $(".dt-scrollable").scrollTop(0);
}