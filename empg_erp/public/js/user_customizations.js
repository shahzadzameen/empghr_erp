frappe.ui.form.on('User',{
    refresh: function(frm){
        // input mask and required for Mobile # for user
         $('input[data-fieldname="mobile_no"]').mask('(+99)9999999999');
         frm.toggle_reqd("mobile_no", true);
    },

    onload: function(frm) {

        if(!frm.is_new()) {

            frm.fields_dict["first_name"].df.read_only = 1;
            frm.fields_dict["middle_name"].df.read_only = 1;
            frm.fields_dict["last_name"].df.read_only = 1;

            frm.fields_dict["middle_name"].refresh();
            frm.fields_dict["first_name"].refresh();
            frm.fields_dict["last_name"].refresh();
    
        }
    }
})
