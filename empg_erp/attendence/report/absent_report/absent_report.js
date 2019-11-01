// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */
frappe.query_reports["Absent Report"] = {
	"filters": [
	    {
        "fieldname": "company",
           "label": __("Select Company"),
           "fieldtype": "Link",
        "options": "Company",
        "on_change": function() {
            scrollTop();
			frappe.query_report.refresh();
			getPagesCount();
			},
        },
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
           "label": __("Select User"),
           "fieldtype": "Select",
           "options": "",
           "placeholder": __("Select User"),
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

			method: "empg_erp.attendence.report.absent_report.absent_report.getPaginationData",
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
                    // user_filter.set_input();
                    $('select[data-fieldname="user"]').val(r.message.default_filter);
			    }
    		    window.pagination.hideDefaultFilter();
                setTimeout(function(){
                    window.pagination.show_limit_paging();
                },250);
			}
		});
	}
}


function getPagesCount() {
		return frappe.call({

			method: "empg_erp.attendence.report.absent_report.absent_report.getPaginationData",
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


function scrollTop(){
    $(".dt-scrollable").scrollTop(0);
}