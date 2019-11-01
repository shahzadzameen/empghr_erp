import frappe
from frappe import _

def autoname_override(self):
	self.name = self.department_name


def before_rename_override(self, old, new, merge=False):
	return new
