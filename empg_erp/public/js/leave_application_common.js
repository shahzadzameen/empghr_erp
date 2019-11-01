frappe.ui.form.on("Leave Application", {
    onload: function(frm){
        frm.trigger("status");
    },

    employee: function(frm){
        frm.trigger("status");
    },

    status: function(frm){
        let islocal = "old"

        if(cur_frm.doc.__islocal && typeof(cur_frm.doc.amended_from)=="undefined"){
            islocal = "new"
        }

        frappe.call({
            method: "empg_erp.modules.common.leave_application.get_leave_status_list",
            args: {
                islocal: islocal,
                employee: cur_frm.doc.employee
            },
            callback : function(res){
                frm.set_df_property('status', 'options', res.message);
                frm.refresh_field('status');
            }
        });
    }
});

