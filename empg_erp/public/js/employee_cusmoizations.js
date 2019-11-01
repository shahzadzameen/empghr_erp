var employee_grid_names = {
                            'education':'Employee Education',
                            'skill_details':'Skills',
                            'external_work_history':'Employee External Work History',
                            'internal_work_history':'Employee Internal Work History',
                            'training_and_certification_details':'Employee Training and Certification',
                            'disability_details':'Employee Disability',
                            'employee_dependents':'Employee Dependent Detail',
                            'address':'Employee Address',
                            'employee_contact_details':'Employee Contact',
                            'employee_documents':'Employee Document',
                            'emergency_contact':'Emergency Contact',
                            'next_of_kin':'Next of Kin',
                          };

var check_is_edit = {};

$(function(){
    $(document).off('keypress','input[data-doctype="Gender"]')
                .on('keypress','input[data-doctype="Gender"]',function(event){
       return window.empg.onlyAlphabets(event,$(this));
    });

    $(document).on("keypress",'input[data-fieldname="employee_number"]',function(e) {
         if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
            return false;
         }
    });
});


frappe.ui.form.on('Employee Address', {
    country: function(frm, dt, dn) {
        var child = locals[dt][dn];
        child.state = child.city = "";
        cur_frm.refresh_field("address");
    },
    state: function(frm, dt, dn) {
        var child = locals[dt][dn];
        child.city = "";
        cur_frm.refresh_field("address");
    }
});

frappe.ui.form.on('Employee',{
    refresh: function(frm){
        frm.set_df_property("employee_number", "read_only", frm.doc.__islocal ? 0:1);
        // input mask for CNIC
        $('input[data-fieldname="cnic"]').mask('99999-9999999-9');
        // Make Fields Mandatory if Active.
        if(frappe.utils.check_is_active("CNIC")){
            frm.toggle_reqd("cnic", frappe.utils.check_is_active("CNIC") == 1);
        }
        if(frappe.utils.check_is_active("EMP_CNIC_EXPIRY")){
            frm.toggle_reqd("cnic_expiry", frappe.utils.check_is_active("EMP_CNIC_EXPIRY") == 1);
        }
        if(frappe.utils.check_is_active("DESIGNATION")){
            frm.toggle_reqd("designation", frappe.utils.check_is_active("DESIGNATION") == 1);
        }
        if(frappe.utils.check_is_active("OFFICE_REGION")){
            frm.toggle_reqd("office_region", frappe.utils.check_is_active("OFFICE_REGION") == 1);
        }
        if(frappe.utils.check_is_active("OFFICE_SUB_REGION")){
            frm.toggle_reqd("office_sub_region", frappe.utils.check_is_active("OFFICE_SUB_REGION") == 1);
        }
        if(frappe.utils.check_is_active("OFFICE_CITY")){
            frm.toggle_reqd("office_city", frappe.utils.check_is_active("OFFICE_CITY") == 1);
        }
        if(frappe.utils.check_is_active("OFFICE_LOCATION")){
            frm.toggle_reqd("office_location", frappe.utils.check_is_active("OFFICE_LOCATION") == 1);
        }
        if(frappe.utils.check_is_active("DIVISION")){
            frm.toggle_reqd("division", frappe.utils.check_is_active("DIVISION") == 1);
        }
        if(frappe.utils.check_is_active("EMPLOYEE_NUMBER")){
            frm.toggle_reqd("employee_number", frappe.utils.check_is_active("EMPLOYEE_NUMBER") == 1);
        }
        if(frappe.utils.check_is_active("LAST_NAME")){
            frm.toggle_reqd("last_name", frappe.utils.check_is_active("LAST_NAME") == 1);
        }
        if(frappe.utils.check_is_active("EMP_EXT_JOB_REASON")){
            frm.fields_dict.external_work_history.grid.toggle_reqd("reason_for_leaving", frappe.utils.check_is_active("EMP_EXT_JOB_REASON") == 1);
        }
        if(frappe.utils.check_is_active("EMPLOYEE_SHIFT_TYPE")){
            frm.toggle_reqd("shift_type", frappe.utils.check_is_active("EMPLOYEE_SHIFT_TYPE") == 1);
        }

        if(frappe.utils.check_is_active("SALUTATION")){
            frm.toggle_reqd("salutation", frappe.utils.check_is_active("SALUTATION") == 1);
        }
        if(frappe.utils.check_is_active("FATHER_NAME")){
            frm.toggle_reqd("father_name", frappe.utils.check_is_active("FATHER_NAME") == 1);
        }
        if(frappe.utils.check_is_active("MARITAL_STATUS")){
            frm.toggle_reqd("marital_status", frappe.utils.check_is_active("MARITAL_STATUS") == 1);
        }
        if(frappe.utils.check_is_active("EMERGENCY_CONTACT")){
            frm.toggle_reqd("emergency_contact", frappe.utils.check_is_active("EMERGENCY_CONTACT") == 1);
        }
        if(frappe.utils.check_is_active("EMP_NOK_TABLE")){
            frm.toggle_reqd("next_of_kin", frappe.utils.check_is_active("EMP_NOK_TABLE") == 1);
        }
        if(frappe.utils.check_is_active("EMP_ADDRESS_GRID")){
            frm.toggle_reqd("address", frappe.utils.check_is_active("EMP_ADDRESS_GRID") == 1);
        }
        if(frappe.utils.check_is_active("EMP_MOTHER_NAME")){
            frm.toggle_reqd("mother_name", frappe.utils.check_is_active("EMP_MOTHER_NAME") == 1);
        }

        if(localStorage) {
            let allowed_doctypes = ''
            allowed_doctypes = localStorage.getItem("allowed_doctypes");
            if(allowed_doctypes &&  allowed_doctypes != '' && allowed_doctypes.length >10){
                frappe.msgprint("Your profile is not upto mark please update.")
            }
        }
    },

    onload: function(){

        frappe.call({
            method:"empg_erp.modules.common.check_is_edit",
            args: {
                employee: cur_frm.doc.employee,
            },
            callback: function(r) {
                if(r.message.disabled){
                    if(r.message.shift_type && r.message.shift_type != undefined){
                        cur_frm.set_df_property("shift_type", "read_only", 1)
                    }else{
                        cur_frm.fields.forEach(function(l){
                            if(l.df.fieldname != 'shift_type')
                                cur_frm.set_df_property(l.df.fieldname, "read_only", 1)
                        });
                    }
                }

                check_is_edit = r;
                employee_grid_readonly();
            }
        });


        // get states of selected country
        cur_frm.fields_dict['address'].grid.get_field('state').get_query = function(doc, dt, dn) {
            var cur_doc = locals[dt][dn];
            var country = cur_doc.country;
            return {
                filters:{"country": country}
            }
        },

        // get cities of selected state
        cur_frm.fields_dict['address'].grid.get_field('city').get_query = function(doc, dt, dn) {
            var cur_doc = locals[dt][dn];
            var state = cur_doc.state;
            return {
                filters:{"state": state}
            }
        }
        
        cur_frm.fields_dict['office_sub_region'].get_query = function(doc, dt, dn) {
            var office_region = doc.office_region;
            if(!office_region){
                frappe.msgprint("Please select Office Region first");
            }
            return {
                filters:{"office_region": office_region}
            }
        }

        cur_frm.fields_dict['office_city'].get_query = function(doc, dt, dn) {
            var office_sub_region = doc.office_sub_region;
            if(!office_sub_region){
                frappe.msgprint("Please select Office Sub Region first");
            }
            return {
                filters:{"office_sub_region": office_sub_region}
            }
        }

        cur_frm.fields_dict['office_location'].get_query = function(doc, dt, dn) {
            var office_city = doc.office_city;
            if(!office_city){
                frappe.msgprint("Please select Office City first");
            }
            return {
                filters:{"office_city": office_city}
            }
        }
    },

    office_region: function(frm, dt, dn){
        frm.fields_dict["office_sub_region"].set_value("");
        frm.fields_dict["office_city"].set_value("");
        frm.fields_dict["office_location"].set_value("");
    },

    office_sub_region: function(frm, dt, dn){
        frm.fields_dict["office_city"].set_value("");
        frm.fields_dict["office_location"].set_value("");
    },

    office_city: function(frm, dt, dn){
        frm.fields_dict["office_location"].set_value("");
    },
    after_save: function(frm){
        //if there is some error then don't call after save
        localStorage.removeItem("allowed_doctypes");
        if (typeof frm.doc.__unsaved == "undefined" || frm.doc.__unsaved != 1){
            frappe.call({
                method:"erpnext.hr.doctype.employee.employee.after_save_employee",
                args: {
                    doctype: frm.doc
                },
                callback: function(r) {
                   frm.reload_doc()
                }
            });
        }
    }

})


function employee_grid_readonly(){
    $.each(employee_grid_names,function(index,ele){
        frappe.ui.form.on(ele, "form_render", function(frm, cdt, cdn) {
            if(check_is_edit.message.disabled){
                if(check_is_edit.message.shift_type == undefined){
                    var docFields = cur_frm.fields_dict[index].grid.docfields;
                    docFields.forEach(function(l){
                        l.read_only = 1;
                        cur_frm.fields_dict[index].grid.refresh(0);
                    });
                }
            }

        });
    });
}