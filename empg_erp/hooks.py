# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version
from utils import get_site_path, import_attr
app_name = "empg_erp"
app_title = "EMPG-ERP"
app_publisher = "zameen"
app_description = "Common HRMS app for EMPG"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "salman.shahid@zameen.com"
app_license = "MIT"


site_dir = get_site_path()
module_name = """empg_erp.modules.{}.hooks""".format(site_dir)

# Includes in <head>
# ------------------


# importing site base settings
app_include_css = import_attr(module_name, "app_include_css", [])
app_include_js = import_attr(module_name, "app_include_js", [])
web_include_js = import_attr(module_name, "web_include_js", [])
website_context = import_attr(module_name, "website_context", {})
doc_events = import_attr(module_name, "doc_events", {})
fixtures = import_attr(module_name, "fixtures", [])
override_whitelisted_methods = import_attr(module_name, "override_whitelisted_methods", {})
scheduler_events = import_attr(module_name, "scheduler_events", {})