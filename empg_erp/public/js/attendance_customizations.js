frappe.ui.form.on('Attendance', {
    onload:function(frm){
var fields_to_disable = ['employee','attendance_status','shift_start_time','shift_end_time','check_in','check_out'];

 frappe.call({
            method:"empg_erp.utils.get_employee_code",
            args: {
            },
            callback: function(r) {
             if(r.message == cur_frm.doc.employee){
             // restrict to update his own attendance and roster
                fields_to_disable.forEach(function(element) {
                    frm.set_df_property(element, "read_only",1);
                });
             }
            }
        });
        frm.fields_dict['attendance_status'].get_query = function(doc, dt, dn) {
            return {
                filters:{"can_assign_manually": 1}
            }
        }
    }
})