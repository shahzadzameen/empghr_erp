// Copyright (c) 2016, zameen and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Company Documents"] = {
	"filters": [
         {
        "fieldname": "Policy_Document_Category",
           "label": __("Select Document Type"),
           "fieldtype": "Link",
        "options": "Policy Document Category",
        "default":function(){
            var type = "";
            if(frappe.user_roles.includes('Line Manager') || frappe.urllib.get_arg("document_type") == frappe.utils.get_config_by_name('EHR_WIDGET_FILTER')){
                type = frappe.urllib.get_arg("document_type");
            }
            return type;
        },
        "get_query": function() {


            if(!frappe.user_roles.filter(value => -1 !== ["HR Manager", "Line Manager", "HR User", "Administrator"].indexOf(value)).length){
                return {
                "doctype": "Policy Document Category",
                "filters": {
                    "name": ["!=", "Line Manager Guides"],
                    }
                }
            }else{
                return {
                    "doctype": "Policy Document Category"
                }
            }
            },

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

    "onload": function(report) {
        if(frappe.user_roles.includes("HR Manager") || frappe.user_roles.includes("HR User")){
            report.page.add_inner_button(__("New"), function() {
                frappe.set_route('Form', 'Policy Document Category/New Company Documents')
		    });
        }

        window.pagination.hideDefaultFilter();
		return frappe.call({

			method: "empg_erp.empg_erp.report.company_documents.company_documents.getPaginationData",
			args: {filters : frappe.query_report.get_filter_values()
			 },
			callback: function(r) {
				var page_filter = frappe.query_report.get_filter('page');
                window.pagination.totalRecords = r.message.totalRecords;
				page_filter.df.options = window.pagination.paginateLimit;
		    	page_filter.refresh();
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
			method: "empg_erp.empg_erp.report.company_documents.company_documents.getPaginationData",
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
