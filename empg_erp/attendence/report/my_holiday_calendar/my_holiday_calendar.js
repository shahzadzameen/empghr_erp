// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["My Holiday Calendar"] = {
	"filters": [
        {
		"fieldname": "page",
		"label": __("Select Page"),
		"fieldtype": "Select",
		"options": "",
		"on_change": function() {
			frappe.query_report.refresh();
			},
	    }
	],
    "onload": function() {
        window.pagination.hideDefaultFilter();
		 getPagesCount();
	}

}


function getPagesCount() {
		return frappe.call({

			method: "empg_erp.attendence.report.my_holiday_calendar.my_holiday_calendar.getPaginationData",
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
}

