// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Attendance Adjustments"] = {
	"filters": [
	    {
			"fieldname":"month",
			"label": __("Select Month"),
			"fieldtype": "Select",
			"options": "",
		},
	     {
	     "fieldname": "type",
           "label": __("Select Type"),
           "fieldtype": "Select",
           "options": "",
        },
	    {
	     "fieldname": "status",
           "label": __("Select Status"),
           "fieldtype": "Select",
           "options": "",
        },
	    {
        "fieldname": "company",
           "label": __("Select Company"),
           "fieldtype": "Link",
        "options": "Company",
        },
	    {
        "fieldname": "department",
           "label": __("Select Department"),
           "fieldtype": "Link",
        "options": "Department",
        },
        {
            "fieldname": "sub_department",
               "label": __("Select Sub Department"),
               "fieldtype": "Link",
            "options": "Department",
            "get_query": function() {
                department = frappe.query_report.get_filter_value("department")
                console.log(department)
                if(department){
                    return {
                    "doctype": "Department",
                    "filters": {
                        "parent_department": ["=", department],
                        }
                    }
                }else{
                    return {
                        "doctype": "Department",
                        "filters": {
                            "parent_department": ["!=", "All Departments"],
                            "parent_department": ["!=", ""]
                        }
                    }
                }
            },
    
            "on_change": function() {
                frappe.query_report.refresh();
                getPagesCount();
                },
        },
	    {
        "fieldname": "employee",
           "label": __("Select Employee"),
           "fieldtype": "Link",
        "options": "Employee",
        },
	    {
        "fieldname": "city",
           "label": __("Select City"),
           "fieldtype": "Link",
        "options": "Office City",
        },
         {
		 "fieldname": "page",
		 "label": __("Select Page"),
		 "fieldtype": "Select",
		 "options": "",
		 "on_change": function() {
		 	frappe.query_report.refresh();
		 	getPagesCount();
		 	},
	      }

	],

	refresh: function(frm) {
	    $('.process-all-btn').remove();
        frm.add_custom_button(__("Load Attachments"), function(foo) {

            frappe.call({
                method:"my_app.my_app.controller.attach_all_docs",
                args: {
                    document: cur_frm.doc,

                },
                callback: function(r) {
                    frm.reload_doc();

                }
            });
        });
    },


	"onload": function(report) {
	        $('.process-all-btn').remove();
            var type_filter = frappe.query_report.get_filter('type');
			type_filter.df.options =["Select Type","Penalty","Reward"];
		    //type_filter.refresh();
			type_filter.set_input();

            var status_filter = frappe.query_report.get_filter('status');
			status_filter.df.options =["Select Status","Unprocessed","Processed"];
		    //status_filter.refresh();
			status_filter.set_input();

			window.pagination.hideDefaultFilter();
            frappe.call({
                method: "empg_erp.attendence.report.absent_report.absent_report.getPaginationData",
                args: {filters : frappe.query_report.get_filter_values()
                },
                callback: function(r) {
                    var page_filter = frappe.query_report.get_filter('page');
                    window.pagination.totalRecords = r.message.totalRecords;
                    page_filter.df.options = window.pagination.paginateLimit;
                    page_filter.refresh();
                    // page_filter.set_input();
                    window.pagination.hideDefaultFilter();
                    setTimeout(function(){
                        window.pagination.show_limit_paging();
                    },250);
                }
            });
			return frappe.call({
	        	method: "empg_erp.attendence.report.attendance_adjustments.attendance_adjustments.getOnloadData",
			    args: {
			        filters : frappe.query_report.get_filter_values()
			    },
			    callback: function(r) {
                    var month_filter = frappe.query_report.get_filter('month');
                    month_filter.df.options = r.message;
                    month_filter.refresh();
                    month_filter.set_input();
                    $('select[data-fieldname="month"]').val(''+r.message[0]);
                    $('select[data-fieldname="status"]').val('Select Status');
                    $('select[data-fieldname="type"]').val('Select Type');
                }
		});

	}

}
function select_all_checkbox(source,empID) {

    if (source.checked) {
        append_process_btn(false);
        $('input[name="emp_action_check"]').each(function () {
            if ($(this).prop('disabled') != true ){
            $(this).prop('checked', true);
            }
        });
    } else {
        append_process_btn(true);
        $('input[name="emp_action_check"]').each(function () {

           if ($(this).prop('disabled') != true ){
            $(this).prop('checked', false);
            }
        });
    }
  }

function process_penalty(emp_id, penalty_id){
    var adjustedPenaltyClass = 'penalty-adjustment-' + emp_id;
    var penalty_adjusted = $("input."+adjustedPenaltyClass).val();

    var data = [{"adjustment" : penalty_adjusted, "id": penalty_id}];

    adjust_penalty(data);

}

function adjust_penalty(data){

    return frappe.call({
        type:'POST',
        method: "empg_erp.modules.mustang.employee_penalty.adjust_penalties",
        args: {"data" : data},
        callback: function(r) {
            frappe.query_report.refresh();
            setTimeout(function(){
                window.pagination.show_limit_paging();
            },250);
        }

    });
}


function reverse_penalty(emp_id, processed_id){

    return frappe.call({
        type:'POST',
        method: "empg_erp.modules.mustang.employee_penalty.reverse_penalties",
        args: {"employee" : emp_id, "processed_id" : processed_id},
        callback: function(r) {
            if('code' in r.message && r.message.code == 200){
                frappe.query_report.refresh();
                setTimeout(function(){
                    window.pagination.show_limit_paging();
                },250);
            }else{
                frappe.throw(r.message.msg)
            }
            
        }

    });
}

function process_penalty_all(){

    var all_checked = $('.individual:checkbox:checked');
    var data = [];

    for (i = 0; i < all_checked.length; i++) {
        var employee_id = $(all_checked[i]).prop('id');
        var penalty_id = $(all_checked[i]).prop('value');

        var adjustedPenaltyClass = 'penalty-adjustment-' + employee_id;
        var penalty_adjusted = $("input."+adjustedPenaltyClass).val();

        data.push({"adjustment" : penalty_adjusted, "id": penalty_id})

    }

    adjust_penalty(data);

}

$(document).on('change','input[name="emp_action_check"]',function(){
    var checked = $('input[name="emp_action_check"]').filter(":checked").length;
    if(checked > 0){
        append_process_btn(false);
    }else{
        append_process_btn(true);
    }
    return;
});

$(document).off('keyup','.penalty-adjustment').on('keyup','.penalty-adjustment', function(e){

   var penaltyAdjustment = parseFloat($(this).val());
   var empId = $(this).prop('id')
   var adjustedPenaltyClass = 'adjusted-penalty' + empId;

   var  adjustedPenalty = $("span."+adjustedPenaltyClass).attr('title');


       if(penaltyAdjustment > adjustedPenalty){
			alert(('Penalty adjustment cannot be greater than actual penalty.'));
			$(this).val('');
	        $("span."+adjustedPenaltyClass).text(adjustedPenalty);
	        return false;
		}
		 if(penaltyAdjustment < 0){
			alert(('Penalty adjustment must be greater than zero.'));
			$(this).val('');
	        $("span."+adjustedPenaltyClass).text(adjustedPenalty);
		    return false;
		}
		if(!isNaN(penaltyAdjustment)){

			var new_penalty_val = adjustedPenalty - penaltyAdjustment;

			$("span."+adjustedPenaltyClass).text(new_penalty_val);
		}
        if(isNaN(penaltyAdjustment)){
			$("span."+adjustedPenaltyClass).text(adjustedPenalty);
		}

});

function append_process_btn(bool){
    $('.process-all-btn').remove();
    if(!bool)
        $('.btn-group.menu-btn-group').before('<button onclick="process_penalty_all()" class="process-all-btn btn-primary btn btn-sm hidden-xs">Process</button>');
}

function getPagesCount() {
		return frappe.call({
			method: "empg_erp.attendence.report.attendance_adjustments.attendance_adjustments.getPaginationData",
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