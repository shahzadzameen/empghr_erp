frappe.ui.form.on('Announcement', {
    refresh: function(frm){
        var cur_url = cur_frm.doc.document
        window.empg.attachment_clickable(cur_url); // Call general function
    }
});