frappe.ui.form.on('User', {
    after_save: function(frm){
        if( !frm.doc.__islocal && frm.doc.email != frm.doc.name ){

            if(frm.doc.name != frm.doc.email){
                frappe.call({
                    method:"frappe.model.rename_doc.rename_doc",
                    freeze: true,
                    args: {
                        doctype: frm.doc.doctype,
                        old: frm.doc.name,
                        "new": frm.doc.email,
                        "merge": 0
                    },
                    callback: function(r,rt) {
                        if(!r.exc) {
                            $(document).trigger('rename', [frm.doc.doctype, frm.doc.name,
                                r.message || frm.doc.email]);
                            if(locals[frm.doc.doctype] && locals[doctype][frm.doc.name])
                                delete locals[frm.doc.doctype][frm.doc.name];
                            d.hide();
                            if(callback)
                                callback(r.message);
                        }
                    }
                });
            }
        }
    }
})