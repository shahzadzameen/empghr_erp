# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SiteConfig(Document):

	def after_insert(self):
		self.update_cache() 

	def on_update(self):
		self.update_cache() 

	def after_delete(self):
		self.update_cache() 

	def update_cache(self):

		_config = frappe.db.get_all("Site Config", {}, ["field", "value", "description", "doc_type"])
		
		frappe.cache().hdel("site_configurations", "config")
		frappe.cache().hset("site_configurations", "config", _config)
		
		return _config