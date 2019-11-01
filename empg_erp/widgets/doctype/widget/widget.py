# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from empg_erp.widgets.doctype.bookmark.template_functions import TemplateFunctions

class Widget(Document):
    	
	def eval_template_function(self, *args, **kwrgs):
    		
		tf = TemplateFunctions(*args, **kwrgs)
		tf.eval_function()
		self.eval_template(tf.__dict__)

	def eval_template(self, data):
    		
		self.template = frappe.render_template("empg_erp/widgets/page/dashboard/component/explorer/{}.html".format(data["template"]), data)
		self.widget_type = data["widget_type"]