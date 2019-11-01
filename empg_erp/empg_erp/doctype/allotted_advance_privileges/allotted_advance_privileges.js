// Copyright (c) 2019, zameen and contributors
// For license information, please see license.txt

frappe.ui.form.on('Allotted Advance Privileges', {
	refresh: function(frm) {

	},
	type: function(frm){
		frm.set_value("privilege_to",'');
	},

});
