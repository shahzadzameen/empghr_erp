// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Attendance Report"] = {
	"filters": [
        {
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"on_change" : function(){
			    scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"on_change" : function(){

				frappe.query_report.get_filter('sub_department').df.read_only = 0;
				frappe.query_report.get_filter("sub_department").value = "";
				frappe.query_report.get_filter('sub_department').refresh();
                scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname":"sub_department",
			"label": __("Sub Department"),
			"fieldtype": "Link",
			"options": "Department",
			"read_only" : 1,
			"get_query" : function(){

				return {
					"doctype" : "Department",
					"filters" : {
						"parent_department" : frappe.query_report.get_filter_value("department")
					}
				}
					
			},
			"on_change" : function(){
			    scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
        "fieldname": "user",
           "label": __("Select User"),
           "fieldtype": "Select",
           "options": "",
           "placeholder": __("Select User"),
        	"on_change": function() {
			    scrollTop();
			    refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			},
        },
		{
			"fieldname":"late_arrival",
			"label": __("Arrived Late By(mins)"),
			"fieldtype": "Data",
			"on_change" : function(){
				scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname":"left_early",
			"label": __("Left Early By(mins)"),
			"fieldtype": "Data",
			"on_change" : function(){
				scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Datetime",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"on_change" : function(){
				scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Datetime",
			"default": frappe.datetime.get_today(),
			"on_change" : function(){
				scrollTop();
				refresh_count();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		},
		{
			"fieldname": "page",
			"label": __("Select Page"),
			"fieldtype": "Select",
			"option" : "",
			"on_change" : function(){
				scrollTop();
				frappe.query_report.refresh();
				set_page_count_onFilterChange();
			}
		}
	],

	"onload": function() {

	    window.pagination.hideDefaultFilter();
		return set_page_count();
	}
}
function select_all_checkbox(source,empID) {
    if (source.checked) {
        append_update_btn(false);
        $('input.individual').each(function () {
            if ($(this).prop('disabled') != true ){
            $(this).prop('checked', true);
            }
        });
    } else {
        append_update_btn(true);
        $('input.individual').each(function () {

           if ($(this).prop('disabled') != true ){
            $(this).prop('checked', false);
            }
        });
    }
  }
function append_update_btn(bool){
    $('.process-all-btn').remove();
    if(!bool)
        $('.btn-group.menu-btn-group').before('<button onclick="attendance_report_action()" class="process-all-btn btn-primary btn btn-sm hidden-xs">Update</button>');

}
$(document).on('change','input.individual',function(){
    var checked = $('input.individual').filter(":checked").length;
    if(checked > 0){
        append_update_btn(false);
    }else{
        append_update_btn(true);
    }
    return;
});
function refresh_count(){
    $(".dt-scrollable").scrollTop(0);
	// $("select[data-fieldname='page']").val("")
}
function set_page_count_onFilterChange(){
	return frappe.call({

		method: "empg_erp.attendence.report.daily_attendance_report.daily_attendance_report.get_count",
		args: {
			filters : frappe.query_report.get_filter_values()
			},
		callback: function(res) {

			page_list = [""]
			if("message" in res){
				for(var i = 0 ; i < res.message.pagination; i++){
					page_list.push(i+1);
				}
			}
			var page_filter = frappe.query_report.get_filter('page');
			window.pagination.totalRecords = res.message.totalRecords;
            page_filter.df.options = window.pagination.paginateLimit;
			page_filter.refresh();
			refresh_count();
			window.pagination.hideDefaultFilter();
            setTimeout(function(){
                window.pagination.show_limit_paging();
            },250);
		}
	});
}
function set_page_count(){
	return frappe.call({

		method: "empg_erp.attendence.report.daily_attendance_report.daily_attendance_report.get_count",
		args: {
			filters : frappe.query_report.get_filter_values()
			},
		callback: function(res) {
			page_list = [""]
			if("message" in res){
				for(var i = 0 ; i < res.message.pagination; i++){
					page_list.push(i+1);
				}
			}
			var page_filter = frappe.query_report.get_filter('page');
			window.pagination.totalRecords = res.message.totalRecords;
            page_filter.df.options = window.pagination.paginateLimit;
			page_filter.refresh();
			refresh_count();
			if(res.message.user === undefined || res.message.user.length == 0){
                        $('select[data-fieldname="user"]').parent().remove();
                }else{
                    var user_filter = frappe.query_report.get_filter('user');
                    user_filter.df.options = res.message.user;
                    user_filter.refresh();
                    user_filter.set_input();
                    $('select[data-fieldname="user"]').val(res.message.default_user_filter);
			    }
			window.pagination.hideDefaultFilter();
            setTimeout(function(){
                window.pagination.show_limit_paging();
            },250);
		}
	});
}



function get_all_checked(){

    var all_checked = $('.individual:checkbox:checked');
    var data = [];

    for (i = 0; i < all_checked.length; i++) {
        var employee_id = $(all_checked[i]).prop('id');
        var attendance_id = $(all_checked[i]).prop('value');
        data.push(attendance_id);

    }

    return (data);

}

function attendance_report_action(event, id, shift_start_time, shift_end_time, attendance_status){

    var all_checked = $('.individual:checkbox:checked');
    if(all_checked.length > 0 || id != null){

        if(shift_start_time == '-')
            shift_start_time = '';
        if(shift_end_time == '-')
            shift_end_time = '';
        var roster_status = [];

        // ROSTER STATUS CALL
        $.ajax({
            url: '/api/resource/Roster Status?fields=["name","title", "can_assign_manually"]',
            type: "GET",
            async:false,
            dataType:"json",
            success:function(r){
                $.each(r.data,function(index,element){
                    if (element.can_assign_manually)
                        roster_status.push(element.name);
                });
            }
        });
        // ROSTER STATUS CALL

        var d = new frappe.ui.Dialog({
            'fields': [
                {'label' : 'Shift Start Time', 'fieldname': 'shift_start_time', 'fieldtype': 'Time', 'default': shift_start_time},
                {'label' : 'Shift End Time','fieldname': 'shift_end_time', 'fieldtype': 'Time', 'default': shift_end_time},
                {'label' : 'Roster Status','fieldname': 'attendance_status', 'fieldtype': 'Select', 'default': attendance_status,'options':roster_status},
            ],
            primary_action: function(){

                _data = d.get_values();
                if(id != null){
                  var list_data = [];
                  list_data.push(id);
                  _data["id"] = list_data;
                }else{
                  _data["id"] = get_all_checked();
                }
                $.ajax({
                    method: "POST",
                    url: "/",
                    headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
                    data: {
                        cmd: "empg_erp.attendence.report.daily_attendance_report.daily_attendance_report.update_attendance_time",
                        data: JSON.stringify(_data)
                    },
                    dataType: "json",
                    success: function(data) {
                        if(data.message.success === undefined || data.message.success == 0){
                            frappe.msgprint(data.message.err);
                        }

                       if(data.message.success !== undefined){
                         var html = "<p>"+data.message.success +" </p>";
				         frappe.msgprint(html, __('Message'));
                       }
                        $('.process-all-btn').remove();
                        d.hide();
                        frappe.query_report.refresh();
                        setTimeout(function(){
                            window.pagination.show_limit_paging();
                        },250);
                    }
                })
            },
            "title":__("Edit Attendance")
        });
        var fields = d.get_values();
        $.each(fields,function(index,ele){
           var field = d.get_field(index);
            field.df.reqd = true;
            field.refresh();
        });
        d.show();
	}
}
function scrollTop(){
    $(".dt-scrollable").scrollTop(0);
}