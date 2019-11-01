$(document).bind('toolbar_setup', function() {

    $('.dropdown-help').hide();
    // hiding erpnext footer link
    $("div.footer-powered a.text-muted").hide();

    $('.navbar-home .erpnext-icon').hide();

    // loading site configurations from cache
    if(!('site_config' in frappe.utils)){
        frappe.call({
            method: "empg_erp.utils.get_site_config",
            args: {},
            callback : function(res){
                
                if('message' in res){

                    frappe.utils['site_config'] = res.message;

                    var site_path = frappe.utils.site_config["site_module"];

                    $('.navbar-home .erpnext-icon').show().attr('src','assets/empg_erp/'+site_path+'/images/erp-icon.png');

                }
            }
    
        });
    }


});

$(document).on('page-change', function(e) {
    $('.process-all-btn').remove();
        
    let allowed_doctypes = null;
    if(localStorage) {
        allowed_doctypes = localStorage.getItem("allowed_doctypes");
        if(allowed_doctypes && window.location.hash != "#login")
            redirect_to_allowed_doctype(allowed_doctypes);
    }
    if(allowed_doctypes == null && window.location.hash != "#login"){
        frappe.call({
            method: "empg_erp.utils.check_doctype_restriction",
            args: {},
            callback : function(res){ 
                let docs = ''; 
                if(res.message.length > 0)
                    docs = JSON.stringify(res.message);
                localStorage.setItem("allowed_doctypes", docs);
                redirect_to_allowed_doctype(docs);
            }
        });
    }

});

function redirect_to_allowed_doctype(allowed_doctypes){
    let curr_url = frappe.get_route_str();
    let redirect = true;
    let redirect_url = false;
    let redirect_doc = frappe.utils.get_config_by_name("DEFAULT_REDIRECT_DOCTYPE","Employee");
    if(allowed_doctypes != '' && allowed_doctypes != null && allowed_doctypes.length >10){
        JSON.parse(allowed_doctypes).forEach(function(doctype){
            if(curr_url.indexOf('/'+doctype.doc+'/') > -1) {
                redirect = false;
            }
            else {
                redirect_url = doctype.url;
            }
        });
        if(redirect === true)
            window.location = redirect_url;
    }
}    
 $(document).ready(function(){
    $('.navbar-brand.ellipsis').attr('style','padding-top:0px !important');
    $('.footer-powered, .footer-subscribe').remove();
});


 frappe.utils.check_is_active = function(name){

    if(!('site_config' in frappe.utils)){
        console.log("Site config is not loaded yet");
        return false;
    }
    let obj = frappe.utils.site_config[name];

    if(typeof obj == "undefined")
        return false;
    
    return !!+obj;

}
   
frappe.utils.get_config_by_name = function(name,default_value = ''){

    if(!('site_config' in frappe.utils)){
        return default_value;
    }
    let obj = frappe.utils.site_config[name];

    if(typeof obj == "undefined")
        return default_value;
    
    return obj;

}
// all our custom js functions and utilities will use this instance
var EMPG = function(){
    this.onlyAlphabets = function(e, t) {
        try {
            if (e) {
                var charCode = e.keyCode;
            }
            else if (e) {
                var charCode = e.which;
            }
            else { return true; }
            if ((charCode > 64 && charCode < 91) || (charCode > 96 && charCode < 123) || charCode == 32)
                return true;
            else
                return false;
        }
        catch (err) {
            frappe.msgprint(err.Description);
        }
    },
    this.show_hide_grid_column = function(frm, childTable, field, show) {

        if (!(childTable in frm.fields_dict))
            return ;

        show = !! + show;
        var grid = frm.fields_dict[childTable].grid;

        if (!(field in grid.fields_map))
            return ;

        grid.fields_map[field].hidden = !show;
        grid.fields_map[field].in_list_view = show;

        grid.visible_columns = false;
        grid.setup_visible_columns();

        grid.form_grid.find("div.grid-row").remove();

        grid.header_row = false;
        grid.make_head();
            
        grid.grid_rows = [];
        grid.refresh();

    },
    this.attachment_clickable = function(url){
        var control_value = $('div[data-fieldtype="Attach"]').find('.control-input-wrapper .control-value');
        var control_input = $('div[data-fieldtype="Attach"]').find('.control-input-wrapper .control-input');
        if(!control_input.find('.btn-attach').html() || control_input.find('.btn-attach').hasClass('hide')){
            control_value.hide();
            var html = '<div class="attached-file" style="display: block;">'+
                    '<div class="ellipsis">'+
                        '<i class="fa fa-paperclip"></i>'+
                        '<a class="attached-file-link" target="_blank" href="'+url+'">'+url+'</a>'+
                    '</div>'+
                '</div>';
            if(control_input.find('.btn-attach').hasClass('hide')){
                $('.attached-file').remove();
                control_input.append(html).show();
            }else{
                control_input.html(html).show();
            }
        }
    },
    this.get_login_emp_code = function(){
        var code = "";
        frappe.call({
            method: "empg_erp.utils.get_employee_code",
            args: {},
            async:false,
            callback : function(res){
                if('message' in res){
                    code = res.message;
                }
            }
        });
        return code;
    }
    this.crete_read_only_field = function (field_name, field_title, display_value){
        return '<div class="frappe-control '+ field_name +'" data-fieldtype="Data" data-fieldname="'+ field_name +'" title="'+ field_name +'">'+
            '<div class="form-group">'+
            '<div class="clearfix">'+
                '<label class="control-label" style="padding-right: 0px;">'+ field_title +'</label>'+
            '</div>'+
            '<div class="control-input-wrapper">'+
                '<div class="control-input" style="display: none;"></div>'+
                '<div class="control-value like-disabled-input" style="">'+ display_value +'</div>'+
                '<p class="help-box small text-muted hidden-xs"></p>'+
            '</div>'+
            '</div>'+
        '</div>';
    }
    this.calculate_time_at_company= function(date_of_joining){
        var douration = moment.duration(moment().diff(moment(date_of_joining)));
        return douration._data.years + ' Year, ' + douration._data.months + ' Months'
    }
}

EMPG.prototype.methods = function(){}
EMPG.prototype.utils = function(){}

window.empg = new EMPG();

