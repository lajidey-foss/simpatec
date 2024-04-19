# Copyright (c) 2023, Phamos GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class SoftwareMaintenance(Document):
	def on_update(self):
		self.update_sales_order()

	def update_sales_order(self):
		if self.sales_order and not self.is_new():
			software_maintenance = frappe.get_cached_value('Sales Order', self.sales_order, 'software_maintenance')
			if software_maintenance and software_maintenance != self.name:
				frappe.throw(_('Software Maintenance already exist for {0}').format(frappe.get_desk_link("Sales Order", self.sales_order)))
			
			if not software_maintenance:
				frappe.db.set_value('Sales Order', self.sales_order, 'software_maintenance', self.name)
				frappe.msgprint(_("This Software Maintenance has been updated in the respective link field in Sales Order {0} ℹ️".format(frappe.get_desk_link("Sales Order", self.sales_order))))

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc
	def postprocess(source, doc):

		doc.sales_order_type = "Other"
		doc.item_group = source.item_group
		doc.customer_subsidiary = source.customer_subsidiary
		doc.software_maintenance = source.name
		doc.append("items",{
			"qty":0
		})

	doc = get_mapped_doc(
		"Software Maintenance",
		source_name,
		{
			"Software Maintenance": {
				"doctype": "Sales Order"
			},
		},
		target_doc,
		postprocess,
	)

	return doc
