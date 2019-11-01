frappe.ui.form.on('Employee External Work History', {

    from_date: function(frm,cdt,cdn){
        check_date_order(frm,cdt,cdn);
    },
    to_date: function(frm,cdt,cdn){
        check_date_order(frm,cdt,cdn);
    }
});

function check_date_order(frm,cdt,cdn){

    var current_item = locals[cdt][cdn];

    if(typeof(current_item.to_date) != "undefined" &&
      current_item.to_date != "" &&
      typeof(current_item.from_date) != "undefined" &&
      current_item.from_date != ""
      ){
        var fDate = moment(current_item.from_date);
        var tDate = moment(current_item.to_date);

        if( tDate <= fDate){
            frappe.model.set_value(cdt, cdn, "to_date", "");
            frappe.throw(("To Date must be grater than From Date"))
            validated = False
            return False
        }
    }
}


frappe.ui.form.on('Employee', {
    refresh: function(frm){
        if(!cur_frm.doc.__islocal){
            frm.trigger("final_confirmation_date");
        }
    },
    onload: function(frm){
        
        frappe.call({
            method:"frappe.client.get_value",
            args: {
                doctype:"Allotted Advance Privileges",
                filters: {
                    privilege: frappe.utils.get_config_by_name('HAS_NO_REPORTS_TO'),
                    privilege_to: frm.doc.name
                },
                fieldname:['name']
            }, 
            callback: function(r) {
                if("message" in r){
                    frm.toggle_reqd("reports_to", false);
                }else{
                    frm.toggle_reqd("reports_to", true);
                }
            }
        });

        if(!cur_frm.doc.__islocal){
            frm.trigger("final_confirmation_date");
        }
        cur_frm.fields_dict['sub_department'].get_query = function(doc, dt, dn) {
            var department = doc.department;
            if(!department){
                frappe.msgprint(__("Please select Department first"));
            }
            return {
                filters:{"parent_department": department}
            }
        }
    },
    department: function(frm, dt, dn){
        frm.fields_dict["sub_department"].set_value("");
    },
    sub_department: function(frm, dt, dn){
        var department = frm.doc.department;
        var sub_department = frm.doc.sub_department;
        if(sub_department != "" && sub_department != undefined){
            frappe.call({
                method:"frappe.client.get_value",
                args: {
                    doctype:"Department",
                    filters: {
                        name:sub_department
                    },
                    fieldname:["parent_department"]
                },
                callback: function(r) {
                    if(department != r.message.parent_department){
                        frm.fields_dict["sub_department"].set_value("");
                    }
                }
            });
        }
    },

    date_of_joining: function(frm){
        let period = parseInt(frappe.utils.get_config_by_name('PROBATION_PERIOD'))
        let probation_end = moment(frm.doc.date_of_joining).add(period, 'days').format('YYYY-MM-DD');
        frm.set_value("final_confirmation_date", probation_end);
        frm.trigger("final_confirmation_date");;
    },
    employment_type: function(frm){
        frm.trigger("final_confirmation_date");
    },
    final_confirmation_date: function(frm){
        // If Employement Type is not Probation, then make probation completion date Read Only
        if(frm.doc.employment_type!=frappe.utils.get_config_by_name('EMPLOYMENT_TYPE_PROBATION',"Probation") &&
         typeof(frm.doc.employment_type) !="undefined" &&
         typeof(frm.doc.date_of_joining) !="undefined"
         ){
            frm.set_df_property("final_confirmation_date", "read_only",1);
            frm.toggle_reqd("final_confirmation_date", false);
        }else{
            frm.set_df_property("final_confirmation_date", "read_only",0);
            frm.toggle_reqd("final_confirmation_date", true);
        }
    }
    
});