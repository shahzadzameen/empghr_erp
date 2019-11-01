frappe.ui.form.on("Leave Application", {
	from_date: function(frm) {
		frm.trigger("half_day");
	},
	to_date: function(frm) {
		frm.trigger("half_day");
	},
	half_day: function(frm) {
		if (frm.doc.half_day && frm.doc.from_date == frm.doc.to_date) {
            cur_frm.set_value("half_day_date", frm.doc.from_date);
		}
	},
});

