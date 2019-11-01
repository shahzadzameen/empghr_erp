# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from bookmark_functions import BookmarkFunctions
from frappe.model.document import Document


class Bookmark(Document):
	
	def get_widget(self, widget_name):
		try:
			return frappe.get_doc("Widget", widget_name)
		except:
			frappe.throw(_("Widget {} not found.".format(widget_name)))

	def get_bookmarks(self, widget_report):
		return frappe.get_all("Bookmark", {"widget_report" : widget_report, "type" : ["!=","Template"]}, ["title","type","value", "params"])

	def evaluate_bookmarks(self, results, query):
		
		bookmark = str()
		
		for result in results:
    		
			execute = BookmarkFunctions(**{
				"type" : result["type"], 
				"value": result["value"], 
				"params" : result["params"]
				}).eval_function()
			bookmark = """'{0}'""".format(execute if execute else 0)

			query = query.replace("""@{0}@""".format(result["title"]), bookmark)
				
		return query

	def get_plane_data(self, query):

		# print("queryyyyyyyyyyyyyyyyyyy")
		# print(query)
		query_chunks = query.strip().split("|||||")
		_chunks = query_chunks[:-1]
		for query_chunk in _chunks:
			
			frappe.db.sql(query_chunk)

		frappe.db.commit()

		return frappe.db.sql(query_chunks[-1], as_dict=True)
		
	
