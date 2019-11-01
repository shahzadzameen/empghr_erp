# -*- coding: utf-8 -*-
# Copyright (c) 2019, zameen and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PolicyDocument(Document):
	pass

@frappe.whitelist()
def get_policy_documents():
    policy_categories = dict()
    pol_documents = frappe.db.get_all("Policy Document",
        {
            "parentfield": "policy_document"
        },["parent","title","description","document","version"])
    if(pol_documents):    
        for pol_document in pol_documents:
            if pol_document.parent not in policy_categories:
                policy_categories[pol_document.parent] = []
            temp_dict = dict()
            temp_dict['title'] = pol_document.title
            temp_dict['description'] = pol_document.description
            temp_dict['document'] = pol_document.document
            temp_dict['version'] = pol_document.version

            policy_categories[pol_document.parent].append(temp_dict)

    return policy_categories