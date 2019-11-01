from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.hr.utils import to_snake_case
from empg_erp.utils import get_config_by_name, get_employee_code, get_prioritized_role
import empg_erp.constants.globals  as _globals


class BookmarkFunctions():
    def __init__(self, *args, **kwargs):

        self.bm_type = kwargs["type"]
        self.bm_value = kwargs["value"]
        self.bm_params = tuple(kwargs["params"].split(",")) if kwargs["params"] else tuple()

    def generic(self):
        return 0
    
    def eval_function(self):

        if "Constant" == self.bm_type:
            return "{}".format(eval("_globals.{}".format(self.bm_value)))
        if "Variable" == self.bm_type:
            return "{}".format(eval(self.bm_value))
        elif "Function" == self.bm_type:
        
            try:
                func_name = to_snake_case(self.bm_value)
                if hasattr(self, func_name):
                    return getattr(self, func_name)(*self.bm_params)
                else:
                    return self.generic()
            except Exception as err:
                frappe.log_error(err)
                frappe.throw("There is a problem against {} bookmark".format(self.bm_value))

    def get_config_by_name(self, *args):
        return get_config_by_name(args[0])
    
    def get_employee_code(self, *args):
        return get_employee_code()

    def get_prioritized_role(self, *args):
        return get_prioritized_role()