from . import __version__ as app_version

app_name = "simpatec"
app_title = "Simpatec"
app_publisher = "Phamos GmbH"
app_description = "Customizations for Simpatec"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "support@phamos.eu"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/simpatec/css/simpatec.css"
# app_include_js = "/assets/simpatec/js/simpatec.js"

# include js, css files in header of web template
# web_include_css = "/assets/simpatec/css/simpatec.css"
# web_include_js = "/assets/simpatec/js/simpatec.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "simpatec/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Customer" : "public/js/customer.js",
    "Issue" : "public/js/issue.js",
    "Sales Order" : "public/js/sales_order.js",
	"Quotation" : "public/js/quotation.js",
	"Opportunity": "public/js/opportunity.js",
	"Purchase Order" : "public/js/purchase_order.js",
	"Sales Invoice" : "public/js/sales_invoice.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

after_migrate = "simpatec.install.after_migrate"
after_install = "simpatec.install.after_migrate"

# Uninstallation
# ------------

before_uninstall = "simpatec.install.before_uninstall"
# after_uninstall = "simpatec.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "simpatec.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Order": {
        "validate": "simpatec.events.sales_order.validate",
		"on_submit": [
            "simpatec.events.sales_order.update_software_maintenance", 
			"simpatec.events.sales_order.update_internal_clearance_status"
            ],
		"on_cancel": "simpatec.events.sales_order.reset_internal_clearance_status"
	},
    "Purchase Order": {
        "on_submit": "simpatec.events.purchase_order.on_submit",
        "validate": "simpatec.events.purchase_order.validate",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"simpatec.events.sales_order.create_followup_software_maintenance_sales_order"
	]
}

# Testing
# -------

# before_tests = "simpatec.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "simpatec.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "simpatec.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["simpatec.utils.before_request"]
# after_request = ["simpatec.utils.after_request"]

# Job Events
# ----------
# before_job = ["simpatec.utils.before_job"]
# after_job = ["simpatec.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"simpatec.auth.validate"
# ]

standard_queries = {
	"Contact": "simpatec.custom_queries.custom_contact_query"
}


fixtures = [
# 	{
# 		'dt': 'DocType Link',
# 		"filters": [["parent", "=", "Contact"], ["parenttype", "=", "Customize Form"], ["custom", "=", "1"]]
# 	}
	
	{
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
			"Quotation-anrede",
			"Quotation-anschreiben_vorlage",
			"Quotation-anschreiben",
			"Quotation-cover_letter_en",
			"Quotation-cover_letter_de",
			"Quotation-cover_letter_fr"
			"Quotation-ignore_cover_language",
			"Item-simpatec",
			"Item-item_type",
			"Sales Order Item-reccuring_maintenance_amount"
                ),
            ]
        ],
    },
]
