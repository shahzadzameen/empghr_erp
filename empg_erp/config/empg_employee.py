from __future__ import unicode_literals

from frappe import _



def get_data():

	return [

		{
			"label": _("Employee Personal Details"),
			"icon": "icon-star",
			"items": [

				{
					"type": "doctype",
					"name": "Emergency Contact",
					"description": _("Emergency Contact"),
				},
                {
					"type": "doctype",
					"name": "Emergency Contact Type",
					"description": _("Emergency Contact Type"),
				},
                {
					"type": "doctype",
					"name": "Employee Address",
					"description": _("Employee Address"),
				},
                {
					"type": "doctype",
					"name": "Employee Address Type",
					"description": _("Employee Address Type"),
				},
                {
					"type": "doctype",
					"name": "Employee Dependent Detail",
					"description": _("Employee Dependent Detail"),
				},
                {
					"type": "doctype",
					"name": "Employee Relation Type",
					"description": _("Employee Relation Type"),
				}
                ,
                {
					"type": "doctype",
					"name": "Employee Contact",
					"description": _("Employee Contact"),
				},
                {
					"type": "doctype",
					"name": "Employee Disability",
					"description": _("Employee Disability"),
				},
                {
					"type": "doctype",
					"name": "Employee Disability Type",
					"description": _("Employee Disability Type"),
				},
                {
					"type": "doctype",
					"name": "Visa Sponsor",
					"description": _("Visa Sponsor"),
				},
                {
					"type": "doctype",
					"name": "Employee Training and Certification",
					"description": _("Employee Training and Certification"),
				}
			]
		},
        {
			"label": _("Employee Company Details"),
			"icon": "icon-star",
			"items": [

				{
					"type": "doctype",
					"name": "Division",
					"description": _("Division"),
				},
                {
					"type": "doctype",
					"name": "Skills",
					"description": _("Skills"),
				},
                {
					"type": "doctype",
					"name": "Employee Document",
					"description": _("Employee Document"),
				},
                {
					"type": "doctype",
					"name": "Standardized Designation",
					"description": _("Standardized Designation"),
				},
                {
					"type": "doctype",
					"name": "Designation Category",
					"description": _("Designation Category"),
				},
                {
					"type": "doctype",
					"name": "Job Title",
					"description": _("Job Title"),
				}
			]
		},

		{

			"label": _("Office Locations"),

			"icon": "icon-list",

			"items": [

				{
					"type": "doctype",
					"name": "Office Region",
					"label": _("Office Region")
				},
                {
					"type": "doctype",
					"name": "Office Sub Region",
					"label": _("Office Sub Region")
				},
                {
					"type": "doctype",
					"name": "Office Location",
					"label": _("Office Location")
				},
                {
					"type": "doctype",
					"name": "Office City",
					"label": _("Office City")
				}

			]

		}

	]