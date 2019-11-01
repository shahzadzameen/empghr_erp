import inspect
import frappe

class ErrorHandler():

    @staticmethod
    def log_error(err):
        
        _path = str(inspect.stack()[1][1])

        frappe.get_doc({
            "doctype" : "Error Log",
            "owner" : "Administrator",
            "error" : err,
            "seen" : 0,
            "method" : _path
        }).save()