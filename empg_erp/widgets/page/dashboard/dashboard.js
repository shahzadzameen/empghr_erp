import_css_and_js = function() {
    frappe.require("assets/empg_erp/css/fullcalendar.min.css");
    frappe.require("assets/empg_erp/js/fullcalendar.min.js");

    frappe.require("assets/empg_erp/js/highcharts.js");
}

var list = birthday_list = upcoming_birthday_list = load_icon = sitePath = '';

frappe.pages['dashboard'].on_page_load = function(wrapper) {
	import_css_and_js();

    if(!('site_config' in frappe.utils)){
        frappe.call({
            method: "empg_erp.utils.get_site_config",
            args: {},
            async:false,
            callback : function(res){
                if('message' in res){
                    frappe.utils['site_config'] = res.message;
                    sitePath = frappe.utils.site_config["site_module"];
                }
            }
        });
    }
    if(('site_config' in frappe.utils)){
        sitePath = frappe.utils.site_config["site_module"];
    }

    if(sitePath != "")
        load_icon = '<img src="assets/empg_erp/'+sitePath+'/images/loading-icon.gif" class="spinner-img" alt="">';
    else
        load_icon = '<i class="fa fa-spinner fa-spin fa-2x spinner-img"></i>';

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true
	});
	var boolean_role = frappe.user_roles.filter(value => -1 !== ["HR Manager","Line Manager"].indexOf(value));
	frappe.breadcrumbs.add("Dashboard");
	wrapper.dashboard = new frappe.Dashboard(wrapper,boolean_role,load_icon, sitePath);
};
frappe.pages['dashboard'].refresh = function(wrapper) {
//	wrapper.dashboard.refresh();
    import_css_and_js();
};

frappe.Dashboard = Class.extend({
	init: function(wrapper,boolean_role,load_icon, sitePath) {
		this.wrapper = wrapper;
		this.boolean_role = boolean_role;
		this.load_icon = load_icon;
		this.site_path = sitePath;

		$('<div id="dashboard-wrapper-div"></div>').appendTo(wrapper.page.main);
		
		this.filters = {};
		if(frappe.user.has_role('HR Manager') && sitePath == "explorer"){
//		    ToDo
		    this.add_filters();
		}
		this.refresh();
	},

	render_dashboard: function(template_data){
		let show_widget = {}
		for(var i = 0; i < template_data.length; i++){
			show_widget[template_data[i]["widget_position"].toLowerCase()] = []
		    var j = 0;
			$(template_data).filter(function(index,element) {
                if(template_data[i]["widget_position"] == element["widget_position"])
                    return widget = show_widget[template_data[i]["widget_position"].toLowerCase()].push(element);
            });
		}
		$("#dashboard-wrapper-div").html(frappe.render_template("dashboard",{loadIcon : this.load_icon, boolean_role : this.boolean_role.length, show_widgets : show_widget}));
	},
	set_filter: function(key, value) {
		this.filters[key].$input.val(value);
	},
	get_user: function() {
		var user = this.filters.user.$input.val();
		return user== __("Select User") + "..." ? null : user;
	},

	add_filters: function() {
		var me = this;

		this.filters.dashboard = this.wrapper.page.add_field({
            fieldname: "hr_filter",
            label: __("Please select"),
            "fieldtype": "Select",
			"options": ["All", "My Team"],
			"default" : "All",
            change: function() {
				me.refresh();
            }
		});

	},

//});

//$.extend(dashboard, {
	refresh: function(wrapper) {
		this.wrapper = $(wrapper);
		this.render();
	},
	render: function() {
		var me = this;
		var fiscal_year = '2016';
		this.addWidget();
	},
	addWidget: function() {
		var me = this;

		let filter = null

		if ("dashboard" in this.filters){
			filter = me.filters.dashboard.$input.val();
		}

		frappe.call({
			module:"empg_erp.widgets",
			page:"dashboard",
			method: "get_widget_name",
			type: "GET",
			args: {
				"_filter" : filter
			},
		    callback: function(r){
				if(!r.exc && r.message){
					me.render_dashboard(r.message);
					$.each(r.message, function(i, data){
						if(data["show_widget"] == true){
							me.getWidget(data);
						}
					});
				}
			}
		});

	},
	getWidget: function(widget) {
		var me = this;
		let filter = null

		if ("dashboard" in this.filters){
			filter = me.filters.dashboard.$input.val();
		}
		frappe.call({
			module:"empg_erp.widgets",
			page:"dashboard",
			method: "get_widget",
		    type: "POST",
			args:{widget: JSON.stringify(widget), _filter : filter},
			dataType: 'json',
		    	callback: function(r){
				if(!r.exc && r.message){
					 me.renderPlaneWidget(r.message["data"]);
						list = $('ul#holiday-list li:gt(4)');       // Number of holidays showing in list

						birthday_list = $('ul#birthday-list li:gt(2)');
						upcoming_birthday_list = $('ul#upcoming-birthday-list li:gt(4)');
						list.hide();
						birthday_list.hide();
						upcoming_birthday_list.hide();
						if($('ul#holiday-list li').length <= 5)
							$('.right-widget-link').remove();

						$('.attachment-list').each(function(index,ele){
							if( $(this).find('li').length < 5){
								$(this).parent().find('.annoucement-link').remove();
							}
						});

						if($('ul#birthday-list li').length <= 3)
							$('.birthday-link').remove();
						if($('ul#upcoming-birthday-list li').length <= 5)
							$('.upcoming-birthday-link').remove();
				}
			}
		});

	},
	renderWidget: function(widget){
		var dashboardJSON = this.getDashboardJSON(widget);
		$("#dashboard").sDashboard({
			dashboardData : dashboardJSON
		});
	},
    //	CREATE CUSTOM WIDGET FOR TEMPLATE
	renderPlaneWidget: function(data){

	    if(data["widget_title"] == "Profile Completion Meter"){
	        frappe.require("assets/empg_erp/js/highcharts.js", () => {
                frappe.require("assets/empg_erp/js/highcharts-more.js", () => {
                    frappe.require("assets/empg_erp/js/solid-gauge.js", () => {
                        $('div[data-name="'+data["widget_title"]+'"]').html(data["template"]);
                    });
                });
            });
	    }else{
			frappe.require("assets/empg_erp/js/highcharts.js", () => {
	            $('div[data-name="'+data["widget_title"]+'"]').html(data["template"]);
	        });
	    }
	},
	//	CREATE Right Side Panel WIDGET FOR TEMPLATE
	renderRightPanelWidget: function(widget,widget_title){
	    $('div[data-name="'+widget_title+'"]').html(widget);
	},
	getDashboardJSON: function(widget){
		if (widget.type === 'table' || widget.type === 'tab'){
			return this.getTableWidget(widget);
		}else if (widget.type === 'chart'){
			return this.getPieChartWidget(widget);
		}

	},
	getTableWidget: function(widget){
		var me = this;
		this.updateColumns(widget);
		var tableWidgetData = {
					"aaData" : widget.data,
					"sDom": 'rtip',
					"aoColumns" : widget.columns,
					"iDisplayLength": 10,
					"bPaginate": true,
					"aaSorting": [],
					"bAutoWidth": true
				};
		var dashboardJSON = [{
					widgetTitle : widget.title,
					widgetId : widget.name,
					widgetType : widget.type,
					enableRefresh : false,
					widgetContent : tableWidgetData,
					widgetHeight : widget.height,
					widgetWidth : widget.width,
					widgetBackgroundColor: widget.background_color
				}];
		return dashboardJSON;

	},
	getPieChartWidget: function(widget){
		var me = this;
		var pieChartOptions = {
				HtmlText : false,
				grid : {
					verticalLines : false,
					horizontalLines : false
				},
				xaxis : {
					showLabels : false
				},
				yaxis : {
					showLabels : false
				},
				pie : {
					show : true,
					explode : 6
				},
				mouse : {
					track : true
				},
				legend : {
					position : "se",
					backgroundColor : "#D2E8FF"
				}
			};
		var chartWidgetData = {
					data : widget.data,
					options : pieChartOptions
				};
		var dashboardJSON = [{
					widgetTitle : widget.title,
					widgetId : widget.name,
					widgetType : widget.type,
					widgetContent : chartWidgetData,
					widgetHeight : widget.height,
					widgetWidth : widget.width,
					widgetBackgroundColor: widget.background_color

				}];
		return dashboardJSON;
	},
	updateColumns: function(widget){

		if (widget.type === 'table'){
			var aoColumns = [];
			$.each(widget.columns, function (idx, column) {
			    var obj = { "sTitle": column };
			    aoColumns[idx] = obj;
			});
			widget.columns = aoColumns;
		} else if (widget.type === 'tab'){
			$.each(widget.data, function (idx, tab) {
				var aoColumns = [];
				$.each(tab.columns, function (cidx, column) {
					var obj = { "sTitle": column };
					aoColumns[cidx] = obj;
				});
				tab.columns = aoColumns;
			});
		}
	},


});


viewMoreHoliday = function(event, idname, type){
    if(type == "birthday_list")
        type = birthday_list;
    else if(type == "upcoming_birthday_list")
        type = upcoming_birthday_list;
    else
        type = list
    if($('ul#'+idname+' li').length >= 1){
        type.slideToggle(400);
        var type = $(event).attr('data-btn-type');
        if(type == "View More")
            $(event).attr('data-btn-type','View Less').html('View Less <i class="fa fa-angle-double-right "></i>');
        else
            $(event).attr('data-btn-type','View More').html('View More <i class="fa fa-angle-double-right "></i>');
    }
    return false;
}
