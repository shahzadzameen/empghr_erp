var default_score = 0;
frappe.ui.form.on('Appraisal', {
    employee: function(frm){
        selectionCheckBox(frm);
        if(typeof(frm.doc.employee) != "undefined" && frm.doc.employee != ""){
            frappe.call({
                "method": "empg_erp.modules.common.appraisal.appraisal.get_employee_details",
                args: {
                    employee: frm.doc.employee,
                },
                callback: function (data) {
                    if(data.message){
                        cur_frm.set_value("joining_date", data.message.joining);
                        cur_frm.set_value("kra_template", "");
                        cur_frm.fields_dict['kra_template'].get_query = function(doc) {
                            return {
                                    filters: { "employment_type": data.message.emp_type }
                                }
                            }
                            cur_frm.refresh_field('kra_template');
                    }
                }
            });
        }
    },
    kra_template: function(frm,cdt,cdn){
        if(typeof(frm.doc.kra_template)!="undefined"){
            showHideEmployeeScore(frm);
            cur_frm.set_value("start_date", "");
            frappe.call({
                "method": "empg_erp.modules.common.appraisal.appraisal.is_self_rated",
                args: {
                    name: frm.doc.kra_template
                },
                callback: function (data) {
                    frm.doc.goals = [];
                    frm.doc.discussions = [];
                    frm.doc.discussion = [];
                  
                    $.when( 
                        erpnext.utils.map_current_doc({

                            method: "empg_erp.modules.common.appraisal.appraisal.fetch_appraisal_template",
                            source_name: frm.doc.kra_template,
                            frm: frm

                        })
                        ).then(function(){

                            if(data.message){
                                window.empg.show_hide_grid_column(frm, "goals", "employee_score", true);
                            }else{
                                window.empg.show_hide_grid_column(frm, "goals", "employee_score", false);
                            }
                        })
                           
                }
            });
        };

        frm.get_field("goals").grid.only_sortable();
        frm.get_field("discussion").grid.only_sortable();
        frm.get_field("discussions").grid.only_sortable();
    },
    
    refresh: function(frm,cdt,cdn){
        selectionCheckBox(frm);
    },

    onload: function(frm,cdt,cdn){
        showHideEmployeeScore(frm);
        selectionCheckBox(frm);
        if(typeof(frm.doc.kra_template)!="undefined"){
            frappe.call({
                "method": "empg_erp.modules.common.appraisal.appraisal.is_self_rated",
                args: {
                    name: frm.doc.kra_template
                },
                callback: function (data) {
                    if(data.message){
                        window.empg.show_hide_grid_column(frm, "goals", "employee_score", true);
                    }else{
                        window.empg.show_hide_grid_column(frm, "goals", "employee_score", false);
                    }
                }
            });

            frm.get_field("goals").grid.only_sortable();
            frm.get_field("discussion").grid.only_sortable();
            frm.get_field("discussions").grid.only_sortable();
        };

        var workflowStateKey = frappe.db.get_value("Workflow State", frm.doc.workflow_state, "key", (r) => {
            if(r == "Reviewed by Employee" && frappe.user.name != "Administrator" && frappe.user_roles.includes('Line Manager')){
                confirmMyReportingManager();
            }
        });
    },

    start_date: function(frm){
        if(typeof(frm.doc.start_date) != "undefined" && frm.doc.start_date != ""){
            if(moment(frm.doc.joining_date) > moment(frm.doc.start_date) ){
                frappe.msgprint(__("Start date cannot be earlier than the date of joining"));
                cur_frm.set_value("start_date", "");
            }else{
                // Checking Due days for Appraisal
                frappe.call({
                    "method": "empg_erp.modules.common.appraisal.appraisal.validate_due_days",
                    args: {
                        employee: frm.doc.employee,
                        kra_template: frm.doc.kra_template
                    },
                    callback: function (data) {
                        if(data){
                            if(!data.message){
                                frappe.msgprint(__("You are not eligible for this appraisal."));
                                cur_frm.set_value("start_date", "");
                            }
                        }
                    }
                });
            }
        }
    }
});

frappe.ui.form.on('Appraisal Goal', {
    employee_score: function(doc,cdt,cdn){
        var d = locals[cdt][cdn];
        if (flt(d.employee_score) < 1 || flt(d.employee_score) > 5) {
            frappe.msgprint(__("Employee Score must be between (1-5)"));
            d.employee_score = default_score;
            refresh_field('employee_score', d.name, 'goals');
        }
    },
    score: function(frm,cdt,cdn){
        frappe.call({
            "method": "empg_erp.modules.common.appraisal.appraisal.can_add_appraisal_score",
            args: {
                employee: frm.doc.employee
            },
            callback: function (data) {
                var d = locals[cdt][cdn];
                if(typeof(data.message)!="undefined" && data.message){
                    if (flt(d.score) < 1 || flt(d.score) > 5) {
                        frappe.msgprint(__("Manager Score must be between (1-5)"));
                        d.score = default_score;
                        refresh_field('score', d.name, 'goals');
                    }
                }else{
                    frappe.msgprint(__("You are not "+ frm.doc.employee_name + "'s reporting manager."));
                    d.score = default_score;
                    refresh_field('score', d.name, 'goals');
                }
            }
        });

    }
});

function showHideEmployeeScore(frm){
    if(typeof(frm.doc.employee) != "undefined" && frm.doc.employee != "" && typeof(frm.doc.kra_template)!="undefined" && frm.doc.kra_template != ""){
        frappe.call({
            "method": "empg_erp.modules.common.appraisal.appraisal.isEmployeeAllowed",
            args: {
                employee: frm.doc.employee
            },
            callback: function (data) {
                if(typeof(data.message)!="undefined" && data.message){
                    var df = frappe.meta.get_docfield("Appraisal Goal", "employee_score", cur_frm.doc.name);
                    df.read_only = 1;
                }else{
                    var df = frappe.meta.get_docfield("Appraisal Goal", "employee_score", cur_frm.doc.name);
                    df.read_only = 0;
                }
            }
        });
    }
}

$(document).off('click','.user-action').on('click','.user-action',function(){
    var refuse_anchor = $(this).find('a.grey-link').text();
    var frm = cur_frm ;

    var workflowStateKey = frappe.db.get_value("Workflow State", frm.doc.workflow_state, "key", (r) => {
        if(refuse_anchor == "Refuse"){
            var d = new frappe.ui.Dialog({
                'fields': [
                    {'fieldname': 'reason', 'fieldtype': 'Text', 'label':"Reason", "mandatory":1}
                ],
                primary_action: function(){
                    if(d.get_field("reason").value !== ""){
                        frappe.call({
                            "method": "empg_erp.modules.common.appraisal.appraisal.refusal_reason",
                            args: {
                                document_name: frm.doc.name,
                                reason: d.get_field("reason").value
                            },
                            callback: function (data) {
                                location.reload();
                            }
                        });
                    }
                    d.hide();
                },
                "title":"Reason For Refusal"
            });
            var field = d.get_field("reason");
            d.show();
        }
        else if((refuse_anchor == "Send to Employee" || refuse_anchor == "Submit to Line Manager") && (r == "Refused" || r == "Draft")){
            if(frappe.user.name != "Administrator"){
                confirmMyReportingManager();
            }
        }
        return false;
    });
});

function selectionCheckBox(frm){
    if(typeof(frm.doc.employee) != "undefined" && frm.doc.employee){
        frappe.call({
            "method": "empg_erp.modules.common.appraisal.appraisal.isEmployeeAllowed",
            args: {
                employee: frm.doc.employee
            },
            callback: function (data) {
                if(typeof(data.message) != "undefined" && data.message){
                    var df = frappe.meta.get_docfield("Appraisal Goals Boolean", "selection", cur_frm.doc.name);
                    df.read_only = 0;
                }else{
                    var df = frappe.meta.get_docfield("Appraisal Goals Boolean", "selection", cur_frm.doc.name);
                    df.read_only = 1;
                }
            }
        });
    }
}

function confirmMyReportingManager(){
                frappe.call({
                "method": "empg_erp.modules.common.appraisal.appraisal.my_reporting_manager",
                args: {
                    employee: cur_frm.doc.employee,
                },
                callback: function (data) {
                    if(typeof(data.message) != "undefined" && data.message){
                            // do nothing
                        }else{
                            // disable the appraisal for the self
                            cur_frm.disable_save();
                            cur_frm.fields.forEach(function(l){ cur_frm.set_df_property(l.df.fieldname, "read_only", 1); })
                        }
                }
            });
}