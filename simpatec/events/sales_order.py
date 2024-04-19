from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import cint, cstr, flt, add_days, add_years, today, getdate
from frappe.model.mapper import get_mapped_doc
import datetime


@frappe.whitelist()
def validate(doc, handler=None):
	if doc.sales_order_type == "Internal Clearance":
		doc.eligable_for_clearance = 0
		doc.internal_clearance_details = ""
	elif doc.eligable_for_clearance:
		doc.sales_order_clearances = []

	validate_duplicate_linked_internal_clearance(doc)


@frappe.whitelist()
def validate_duplicate_linked_internal_clearance(doc):
	linked_so = []
	if doc.sales_order_type == "Internal Clearance":
		for so in doc.sales_order_clearances:
			so_clearances = frappe.get_all("Sales Order Clearances", filters={
					"sales_order":so.sales_order, 
					"parent":["!=", doc.name],
					"docstatus": ["!=", 2]
				})
			if len(so_clearances) > 0:
				linked_so.append(so.sales_order)

	if len(linked_so) > 0:
		linked_so = " <br>".join(linked_so)
		frappe.throw("Cannot be linked because these Sales Order are already linked in Different Clearances <br> {0}".format(linked_so))



@frappe.whitelist()
def reset_internal_clearance_status(doc, handler=None):
	if doc.sales_order_type == "Internal Clearance":
		for so in doc.sales_order_clearances:
			so_doc = frappe.get_doc("Sales Order", so.sales_order)
			if so_doc.clearance_status == "Cleared":
				frappe.db.set_value(so_doc.doctype, so_doc.name, "clearance_status", "Not Cleared")


@frappe.whitelist()
def make_software_maintenance(source_name, target_doc=None):
	def postprocess(source, doc):
		if source.sales_order_type == "First Sale":
			doc.first_sale_on = source.transaction_date
		doc.assign_to = source.assigned_to

	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Software Maintenance",
				"field_map": {
					"name": "sales_order",
				},
			},
			"Sales Order Item": {
				"doctype": "Software Maintenance Item",
			},
		},
		target_doc,
		postprocess,
	)

	return doc

@frappe.whitelist()
def update_internal_clearance_status(doc, handler=None):
	if doc.sales_order_type == "Internal Clearance":
		for item in doc.items:
			internal_so = doc.sales_order_clearances[item.idx - 1].get("sales_order")
			frappe.db.set_value(doc.doctype, internal_so, "clearance_status", "Cleared")


def update_software_maintenance(doc, method=None):
	if doc.get("software_maintenance"):
		software_maintenance = frappe.get_doc("Software Maintenance", doc.software_maintenance)
		software_maintenance.performance_period_start = doc.performance_period_start
		software_maintenance.performance_period_end = doc.performance_period_end
		software_maintenance.sale_order = doc.name
		for item in doc.items:
			for sitem in software_maintenance.item:
				if (item.item_code == sitem.item_code):
					sitem.start_date = item.start_date
					sitem.end_date = item.end_date
					break
				else:					
					software_maintenance.append("items", {
						"item_code": item.item_code,
						"item_name": item.item_name,
						"description": item.description,
						"start_date": item.start_date,
						"end_date": item.end_date,
						"price_list_rate": item.price_list_rate,
						"conversion_factor": item.conversion_factor,
						"item_language": item.item_language,
						"rate": item.rate,
						"qty": item.qty,
						"uom": item.uom
					})

		software_maintenance.save()


def create_followup_software_maintenance_sales_order(date=None):
	if not date:
		date = today()

	software_maintenance_list = frappe.db.sql("""
		SELECT name 
		FROM `tabSoftware Maintenance`
		WHERE DATE_SUB(performance_period_end, INTERVAL lead_time DAY) = %s
	""", date, as_dict=1)

	for software_maintenance in software_maintenance_list:
		try:
			make_sales_order(software_maintenance.name)
		except Exception as e:
			error_message = frappe.get_traceback()+"{0}\n".format(str(e))
			frappe.log_error(error_message, 'Error occured While automatically Software Maintenance Sales Order for {0}'.format(software_maintenance))
		finally:
			frappe.db.commit()


@frappe.whitelist()
def make_sales_order(software_maintenance, is_background_job=True):
	software_maintenance = frappe.get_doc("Software Maintenance", software_maintenance)
	if not software_maintenance.assign_to:
		frappe.throw(_("Please set 'Assign to' in Software maintenance '{0}'").format(software_maintenance.name))

	employee =  frappe.get_cached_value('Employee', {'user_id': software_maintenance.assign_to}, 'name')
	if not employee:
		frappe.throw(_("User {0} not set in Employee").format(software_maintenance.assign_to))

	performance_period_start = add_days(software_maintenance.performance_period_end, 1)
	performance_period_end = add_years(performance_period_start, software_maintenance.maintenance_duration)
	total_days = getdate(performance_period_end) - getdate(performance_period_start)

	days_diff = total_days.days%365
	if days_diff != 0:
		performance_period_end = add_days(performance_period_end, -days_diff)
		total_days = getdate(performance_period_end) - getdate(performance_period_start)

	transaction_date = add_days(performance_period_end, -cint(software_maintenance.lead_time))
	sales_order = frappe.new_doc("Sales Order")
	sales_order.customer_subsidiary = software_maintenance.customer_subsidiary
	sales_order.performance_period_start = performance_period_start
	sales_order.performance_period_end = performance_period_end
	sales_order.software_maintenance = software_maintenance.name
	sales_order.item_group = software_maintenance.item_group
	sales_order.customer = software_maintenance.customer
	sales_order.sales_order_type = "Follow Up Maintenance"
	sales_order.ihr_ansprechpartner = employee
	sales_order.transaction_date = transaction_date
	sales_order.order_type = "Sales"

	for item in software_maintenance.items:
		sales_order.append("items", {
			"item_code": item.item_code,
			"item_name": item.item_name,
			"description": item.description,
			"conversion_factor": item.conversion_factor,
			"qty": item.qty,
			"rate": item.rate,
			"uom": item.uom,
			"item_language": item.item_language,
			"delivery_date": sales_order.transaction_date
		})

	sales_order.insert()

	if not cint(is_background_job):
		frappe.msgprint("Maintenance Duration (Years): {}".format(software_maintenance.maintenance_duration))
		frappe.msgprint("Maintenance Duration (Days): {}".format(total_days.days))
		frappe.msgprint(_("New {} Created").format(frappe.get_desk_link("Sales Order", sales_order.name)))

#auto maintenance order
@frappe.whitelist()
def make_maintenance_order(data, tran_data):
	if isinstance(data, str):
		data = json.loads(data)
	data = frappe._dict(data)
	new_subscription_date = tran_data #"1-04-2023"
    
	order_list = frappe.get_list('Sales Order',filters={
		'order_type': 'Sales', 'docstatus': 1, 'customer': data.customer, 'software_maintenance': data.software_maintenance
	},
	fields=['name'],
	order_by='transaction_date desc',
	as_list=True)
	#sales_order.order_type = "Maintenance"

	if (not order_list):
		return

	order_count = len(order_list)
	postion_list, maintenance_list,merge_list = [],[],[]
	first_end_period = 0
	
	if (not order_count > 0):
		return
	for ls in order_list:
		ps ="".join(ls)
		
		print('===================================================================')
		#print(f'\n\n\n show parent  : {ps} \n')
		item_data = frappe.db.sql("""
		SELECT docstatus, idx, item_code,delivery_date, item_name, description,item_group,qty,stock_uom, uom, conversion_factor,rate,amount,transaction_date,parent,start_date,end_date 
		FROM `tabSales Order Item` WHERE parent = '{0}' AND docstatus = 1 ORDER BY idx
		""".format(ps), as_dict=1,)
		maintence_total = 0.0
		if(len(item_data) <= 0):
			return
		#get postion item
		count = len(item_data)
		print(f'\n count {count} \n')
		
		for p in range(count):
			if (p == count-1):
				print(f'\n item maintenance {item_data[p].item_code} \n')
				mlist = item_data[p]

				# check for partail billing
				#print(f'\n loop position  : {item_data[p].item_code} and {item_data[p].rate} \n')
				print(f'\n maintenance length {len(maintenance_list)} \n')
				if(len(maintenance_list)> 0):
					print(f'\n maintenance avaible {maintenance_list} \n')
					#get status from partial bill table 
					partial_maintenance = frappe.db.sql("""
					SELECT party,item_code,transaction_date,sales_order,start_date,end_date,percentage_to_bill,position_item 
					FROM `tabPartial Billing` WHERE sales_order = '{0}' AND item_code = '{1}' AND party = '{2}'
					""".format(mlist.parent,mlist.item_code,data.customer), as_dict=1,)
					# check within target period
					if(partial_maintenance):
						print(f'\n avaible {partial_maintenance} \n')
						if (getdate(partial_maintenance[0].start_date) <= getdate(new_subscription_date) <= getdate(partial_maintenance[0].end_date)):
							#print(f'\n\n lks   : {partial_maintenance}  \n {partial_maintenance[0].sales_order} \n\n {partial_maintenance[0].position_item} \n\n')						
							mlist.item_code = "Maintenance positions Others" 
							mlist.item_name = "Maintenance Positions Others"
							mlist.description = partial_maintenance[0].sales_order +" for " + partial_maintenance[0].position_item
							mlist.rate =  flt(partial_maintenance[0].percentage_to_bill) * maintence_total
							print(f'\n i was here now \n')
						else:
							print(f'\n not sure avaible  \n')
							mlist.rate = maintence_total
					# else:
						# print(f'\n\n diff in months   : {mlist.item_code} and  \n {mlist} \n\n')
						# mlist.rate = maintence_total
					# check here for issue if no partial billing or second patial billing
				else:
					#more work here
					mlist.rate = maintence_total
					#print(f'\n\n i got heree : {maintence_total} \n\n')
				
				#print(f'\n loop position  : {item_data[p].item_code} and {item_data[p].rate} \n')				
				#mlist.rate = maintence_total
				maintenance_list.append(item_data[p])
			else:
				maintence_total += item_data[p].amount
				#print(f'\n maintence total  : {item_data[p].amount} and {maintence_total} \n')
				plist = item_data[p]
				#print(plist)
				plist.rate = 0.0
				plist.amount = 0.0
				postion_list.append(plist)
	#print(f' position  : {postion_list} \n')
	#print(f'\n\n\n maintenance  : {maintenance_list} \n\n')
	#merge double line for maintenance
	pop_index = 100
	for i in range(1, len(maintenance_list)):
		if (maintenance_list[0].item_code == maintenance_list[i].item_code):
			maintenance_list[0].rate = maintenance_list[0].rate + maintenance_list[i].rate
			maintenance_list[i].rate = 0
			maintenance_list[i].qty = 0
			#pop_index = i
			maintenance_list.pop(i)
			#break
	
	merge_list = postion_list + maintenance_list
	#print(f'\n\n merge  : {merge_list} \n')

	""" for itm in merge_list:
		print(f'item is : {itm.item_code} \n') """

	#print(f'\n show me  : {merge_list} \n\n')

	employee =  frappe.get_cached_value('Employee', {'user_id': data.assign_to}, 'name')
	if not employee:
		frappe.throw(_("User {0} not set in Employee").format(software_maintenance.assign_to))

	sales_order = frappe.new_doc("Sales Order")
	sales_order.customer_subsidiary = data.customer_subsidiary
	sales_order.performance_period_start = getdate(new_subscription_date)
	sales_order.performance_period_end = getdate(add_years(new_subscription_date, 1))
	sales_order.item_group = data.item_group
	sales_order.customer = data.customer
	sales_order.ihr_ansprechpartner = employee
	sales_order.transaction_date = getdate(new_subscription_date)
	sales_order.delivery_date = getdate(new_subscription_date)
	sales_order.order_type = "Maintenance"
	for itm in merge_list:
		sales_order.append("items", {
			"item_code": itm.item_code,
			"item_name": itm.item_name,
			"description": itm.description,
			"conversion_factor": itm.conversion_factor,
			"qty": itm.qty,
			"rate": itm.rate,
			"uom": itm.uom,
			"delivery_date": sales_order.transaction_date
		})
	sales_order.insert()

	frappe.msgprint(_("New {} Created").format(frappe.get_desk_link("Sales Order", sales_order.name)))

def update_billing_status(doc, method=None):
	
	def get_first_order(entity):
		#order = frappe.get_doc("Sales Order", doc.software_maintenance)
		order = frappe.get_list('Sales Order', filters={
			'docstatus':1, 'customer': entity, 'sales_order_type':'First Sale'
		},
		fields=['performance_period_end'],
		as_list=True)
		end_p =""
		for ls in order:
			end_p = ls[0]
			print(f'\n\n jole: {getdate(end_p)} \n\n')
		return getdate(end_p)


	if doc.get("software_maintenance"):
		count = len(doc.items)
		
		software_maintenance = frappe.get_doc("Software Maintenance", doc.software_maintenance)
		#first_end_period = get_first_order(doc.customer).strftime('%B')
		first_end_period = get_first_order(doc.customer) 
		for_pein = getdate(doc.performance_period_end)
		print('\n *************************************************************** \n')
		#interval_months = calculate_month_interval(getdate(doc.performance_period_end).strftime('%B'), first_end_period)
		interval_months = check_to_adjust(getdate(doc.performance_period_end), first_end_period)
		part_billing = frappe.new_doc("Partial Billing")
		part_billing.party = doc.customer
		part_billing.transaction_date = doc.transaction_date
		part_billing.sales_order = doc.name
		part_billing.start_date = software_maintenance.performance_period_start #work on this
		part_billing.end_date = software_maintenance.performance_period_end #work on this 
		part_billing.percentage_to_bill = interval_months * (1/12)
		for im in range(count):
			if (im == count-1):
				part_billing.item_code = doc.items[im].item_code
			else:
				part_billing.position_item = doc.items[im].item_code
			
		part_billing.save()

def check_to_adjust(from_month, to_month):
	from dateutil.relativedelta import relativedelta

	month_to_number = {
		"January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
	}
	from_month_num = from_month.strftime('%B')
	to_month_num = to_month.strftime('%B')
	
	try:
		start_number = month_to_number.get(from_month_num.capitalize())
		end_number = month_to_number.get(to_month_num.capitalize())
		print(f' startxx :{start_number} and endxx : {end_number} \n\n\n\n')
		if (start_number > end_number):
			to_month = to_month + relativedelta(years=1)
		start_date = from_month 
		end_date = to_month 
		print(f' begin :{start_date} and finish : {end_date} \n\n\n\n')
		current_date = start_date
		interval = 0

		while current_date < end_date:
			#print(current_date.strftime("%d-%m-%Y"))
			interval += 1
			current_date += relativedelta(months=1)
			print(f'\n thsis {current_date} andyy {interval} \n')
		
		return interval -1

	except KeyError:
		raise ValueError("Invalid month name. Please provide valid month names.")