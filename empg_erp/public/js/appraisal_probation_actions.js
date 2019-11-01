
frappe.ui.form.on('Appraisal' ,{

    kra_template : function(frm){

        if(frm.doc.kra_template){

            frappe.call({
                method: 'frappe.desk.form.load.getdoc',
                type: "GET",
                args: {
                    doctype: "Appraisal Template",
                    name: frm.doc.kra_template
                },
                freeze: true,
                callback: function(r) {
                    
                    if(typeof r.docs[0] !== "undefined"){
    
                        let doc = r.docs[0];
    
                        if(doc["employment_type"] != frappe.utils.site_config["EMPLOYMENT_TYPE_PROBATION"])
                            cur_frm.fields_dict["probation_completion"].df.hidden = 1;
                        else
                            cur_frm.fields_dict["probation_completion"].df.hidden = 0;

                        cur_frm.refresh_field("probation_completion");

                    }
                }
    
            });
        }
        
    },
    probation_completion : function(frm){
        if(cur_frm.doc.probation_completion == "Extend"){
            cur_frm.toggle_reqd("probation_extension_months", 1);
        }else{
            cur_frm.toggle_reqd("probation_extension_months", 0);
        }
    },
    onload : function(frm){
        cur_frm.toggle_reqd("probation_completion", 1);
        if(!frm.is_new()){
            cur_frm.fields_dict["probation_completion"].df.read_only = 1;
            cur_frm.fields_dict["probation_extension_months"].df.read_only = 1;
            cur_frm.refresh_field("probation_completion");
            cur_frm.refresh_field("probation_extension_months");
        }

    }
});