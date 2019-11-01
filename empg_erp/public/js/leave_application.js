var total_days_call = false;

frappe.ui.form.on("Leave Application", {
	refresh: function(frm){

		// procedure to remove default or native event of form events which not turning off by 'frappe.ui.form.off("Leave Application","calculate_total_days")'
		let doctype = "Leave Application";
		let fieldname = "calculate_total_days";
		frappe.ui.form.handlers[doctype][fieldname] = [];
		delete cur_frm.events[fieldname];
		delete cur_frm.cscript[fieldname];

		if (frm.is_new()) {
			frm.trigger("calculate_total_days_ovr");
		}

		// Readonly all fields except new leave application
		if(typeof frm.doc.__islocal === 'undefined'){
			var req_fields = ['status','leave_approver_comments'];
			frm.fields.forEach(function(l){
					if(!req_fields.includes(l.df.fieldname))
						frm.set_df_property(l.df.fieldname, 'read_only', 1);
			});
			frm.trigger("make_dashboard");
		}

		// frm.trigger("status");
		var from_date_datepicker = frm.fields_dict.from_date.datepicker;
		var to_date_datepicker = frm.fields_dict.to_date.datepicker;
		cur_frm.set_df_property("leave_approver", "read_only", true);
		frappe.call({
			method: 'empg_erp.utils.check_advance_privilege_by_name',
			args: {
				name: frappe.utils.get_config_by_name('ADVANCE_PRIV_APPLY_LEAVE_AFTER_CUTOFF_DATE')
			},
			callback: function(r) {
				if (r) {
					// Restricted Date
					var restrictedDate = moment().format("YYYY-MM-"+parseInt(frappe.utils.get_config_by_name('RESTRICTED_LEAVES_DATE',22)));
					
					// Month Processing Date
					var monthProcDate = moment().format("YYYY-MM-"+(parseInt(frappe.utils.get_config_by_name('MONTH_PROCESSING_DATE',20))+1));

					// check if monthProcDate if greater than current date 
					if(restrictedDate > moment().format("YYYY-MM-DD"))
						monthProcDate = moment(monthProcDate).subtract(1, 'months').format('YYYY-MM-DD');
					
					// check if advance privilege for cutoff date 
					if(r.message == true)
						monthProcDate = moment(monthProcDate).subtract(1, 'months').format('YYYY-MM-DD');

					to_date_datepicker.update({
						minDate: frappe.datetime.str_to_obj(monthProcDate)
					});
					from_date_datepicker.update({
						minDate: frappe.datetime.str_to_obj(monthProcDate)
					});
				}
			}
		});

	},
    leave_type: function(frm) {
        frm.trigger("get_leave_type_details");
	},
    validate: function(frm) {
        frm.toggle_reqd("half_day_date", frm.doc.half_day == 1);
        frm.toggle_reqd("hourly_day_date", frm.doc.hourly == 1);
	},
	from_date: function(frm) {
	    if(frm.doc.from_date == frm.doc.to_date){
			frm.set_value('half_day_date',frm.doc.from_date);
			frm.set_value('hourly_day_date',frm.doc.from_date);
		}

		frm.trigger("hourly_day_datepicker");
		frm.trigger("calculate_total_days_ovr");
	},
	to_date: function(frm) {
	    if(frm.doc.from_date == frm.doc.to_date){
			frm.set_value('half_day_date',frm.doc.from_date);
			frm.set_value('hourly_day_date',frm.doc.from_date);
		}
		frm.trigger("hourly_day_datepicker");
		frm.trigger("calculate_total_days_ovr");
	},
	half_day_date(frm) {
		frm.trigger("calculate_total_days_ovr");
		if(frm.doc.from_date == frm.doc.to_date){
			frm.set_value('half_day_date',frm.doc.from_date);
		}
	},
	hourly_day_date: function(frm){
		frm.trigger("calculate_total_days_ovr");
		if(frm.doc.from_date == frm.doc.to_date){
			frm.set_value('hourly_day_date',frm.doc.from_date);
		}
	},
	half_day: function(frm) {
		if (frm.doc.from_date == frm.doc.to_date) {
			frm.set_value("half_day_date", frm.doc.from_date);
		}
		else {
			frm.trigger("half_day_datepicker");
		}
		frm.trigger("calculate_total_days_ovr");
	},
    hourly: function(frm) {
		if (frm.doc.from_date == frm.doc.to_date) {
			frm.set_value("hourly_day_date", frm.doc.from_date);
		}
		else {
			frm.trigger("hourly_day_datepicker");
		}
		frm.trigger("calculate_total_days_ovr");
	},
	hours: function(frm) {
		frm.trigger("calculate_total_days_ovr");
	},
    hourly_day_datepicker: function(frm) {
		frm.set_value('hourly_day_date', '');
		var hourly_day_datepicker = frm.fields_dict.hourly_day_date.datepicker;

		hourly_day_datepicker.update({
			minDate: frappe.datetime.str_to_obj(frm.doc.from_date),
			maxDate: frappe.datetime.str_to_obj(frm.doc.to_date)
		})
	},
	half_day_datepicker: function(frm) {
		frm.set_value('half_day_date', '');
		var half_day_datepicker = frm.fields_dict.half_day_date.datepicker;
		half_day_datepicker.update({
			minDate: frappe.datetime.str_to_obj(frm.doc.from_date),
			maxDate: frappe.datetime.str_to_obj(frm.doc.to_date)
		})
	},
	status: function(frm){
		if(frm.doc.status == 'Open' || frm.doc.status == 'Approved'){
			frm.toggle_reqd("leave_approver_comments",false);
		}else{
			frm.toggle_reqd("leave_approver_comments",true);
		}	
	},
    get_leave_type_details: function (frm){
        frappe.call({
            method:"frappe.client.get_value",
            args: {
                doctype:"Leave Type",
                filters: {
                    leave_type_name:frm.doc.leave_type
                },
                fieldname:["is_hourly","is_halfday"]
            }, 
            callback: function(r) { 
                if(r){
                    // show/hide hourly and half day checkboxes on there settings
					frm.toggle_display("half_day", r.message.is_halfday);
					frm.toggle_display("hourly", r.message.is_hourly);
					
					// Uncheck checkbox
					frm.set_value("hourly", 0);
					frm.set_value("half_day", 0);
                }

            }
        });
    },
    calculate_total_days_ovr: function(frm) {

		if(frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type) {

			var from_date = Date.parse(frm.doc.from_date);
			var to_date = Date.parse(frm.doc.to_date);

			if(to_date < from_date){
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value('to_date', '');
				return;
			}

			if(total_days_call == true){
				return;
			}
			total_days_call = true;

				// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
				args: {
					"employee": frm.doc.employee,
					"leave_type": frm.doc.leave_type,
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"half_day": frm.doc.half_day,
                    "half_day_date": frm.doc.half_day_date,
                    "hourly": frm.doc.hourly,
                    "hourly_day_date": frm.doc.hourly_day_date,
                    "hours": frm.doc.hours,
				},
				callback: function(r) {
					total_days_call = false;
					if (r) {
						frm.set_value('total_leave_days', r.message);
						frm.trigger("get_leave_balance");
					}
				}
			});
		}
	}
});

