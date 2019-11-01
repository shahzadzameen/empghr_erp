frappe.ui.form.on("Policy Document", "form_render", function(frm, cdt, cdn) {
     var cur_url = cur_frm.cur_grid.doc.document;
     window.empg.attachment_clickable(cur_url); // Call general function
});