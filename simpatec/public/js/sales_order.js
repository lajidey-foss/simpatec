frappe.ui.form.on('Sales Order', {
    onload(frm){
        // FILTER SALES ORDER WITH RESPECTIVE CONDITIONS
        frm.set_query('sales_order', 'sales_order_clearances', function () {
            return {
                filters: {
                    "eligable_for_clearance": 1,
                    "clear_by": frm.doc.company,
                    "docstatus": 1,
                    "clearance_status": ["!=", "Cleared"]
                },
            };
        });
    },
    setup: function(frm){
		frm.copy_from_previous_row = function(parentfield, current_row, fieldnames){
			

			var data = frm.doc[parentfield];
			let idx = data.indexOf(current_row);
			if (data.length === 1 || data[0] === current_row) return;
			
			if (typeof fieldnames === "string") {
				fieldnames = [fieldnames];
			}			
			
			$.each(fieldnames, function (i, fieldname) {
				frappe.model.set_value(
					current_row.doctype,
					current_row.name,
					fieldname,
					data[idx - 1][fieldname]
				);
			});
		},
		frm.auto_fill_all_empty_rows = function(doc, dt, dn, table_fieldname, fieldname) {
			var d = locals[dt][dn];
			if(d[fieldname]){
				var cl = doc[table_fieldname] || [];
				for(var i = 0; i < cl.length; i++) {
					if(cl[i][fieldname]) cl[i][fieldname] = d[fieldname];
				}
			}
			refresh_field(table_fieldname);
		},
		frm.occurence_len = function(arr, element){
			
			return arr.filter(
				(ele) => ele.item_language == element
			).length;
		}
	},

    refresh(frm) {
        // GET SIMPATEC GLOBAL SETTINGS
        frm.events.get_simpatec_settings(frm)

        $('[data-doctype="Software Maintenance"]').find("button").hide();
        if (['First Sale', 'RTO', 'Subscription Annual'].includes(frm.doc.sales_order_type) && frm.doc.docstatus == 1 && !frm.doc.software_maintenance) {
            frm.add_custom_button('Software Maintenance', function () { 
                frappe.model.open_mapped_doc({
                    method: "simpatec.events.sales_order.make_software_maintenance",
        			frm: frm
        		})                
            }, __("Create"));
        }

        // MAKE TABLE FULL WIDTH
        if(frm.doc.sales_order_type == "Internal Clearance"){
            $("div[data-fieldname='sales_order_clearances']").parents(".form-column").addClass("col-md-12")
        }else {
            $("div[data-fieldname='sales_order_clearances']").parents(".form-column").removeClass("col-md-12")
        }

    },

    get_simpatec_settings(frm){ // SIMPATECH GLOBAL SETTING FUNCTION
        frm.doc.clearance_item = ""
        frm.call({
            method: "frappe.client.get",
            args: {
                fieldname: "clearance_item",
                doctype: "SimpaTec Settings"
            },
            async: false,
            callback: function (r) {
                if (r.message) {
                    frm.doc.clearance_item = r.message.clearance_item; // SET CLEARANCE ITEM IN GLOBAL FRM VARIABLE.
                }
            }
        });
    },
    eligable_for_clearance(frm){ // ELIGIBLE FOR CLEARANCE CHECK FUNCTIONALITY
        // SET CLEAR BY REQUIRED IF ELIGABLE FOR CLEARANCE IS CHECKED
        if (frm.doc.eligable_for_clearance){
            frm.toggle_reqd("clear_by", 1)
        }else{
            frm.toggle_reqd("clear_by", 0)
        }
    },
    sales_order_type(frm){
        // MAKE TABLE FULL WIDTH
        if(frm.doc.sales_order_type == "Internal Clearance"){
            $("div[data-fieldname='sales_order_clearances']").parents(".form-column").addClass("col-md-12")
        }else{
            $("div[data-fieldname='sales_order_clearances']").parents(".form-column").removeClass("col-md-12")
        }
    },

})

// SALES ORDER CLEARANCE TABLE EVENTS
frappe.ui.form.on("Sales Order Clearances", {
    sales_order_clearances_add(frm, cdt, cdn){ // EVENT TRIGGER ON ADD ROW
        var cur_row = locals[cdt][cdn];
        if(!is_null(frm.doc.customer)){ // CHECK IF CUSTOMER IS EMPTY

            // CHECK THE SAME ROW INDEX OF ITEM TABLE, IF ROW IS NOT AVAILABLE 
            // THEN ADD NEW ROW IN ITEM TABLE, OTHERWISE UPDATE THE EXISTING INDEX ROW
            var item_row = frm.doc.items[cur_row.idx - 1];  // GET THE ITEM TABLE SAME ROW INDEX
            if (!is_null(item_row)) {
                // UPDATING SAME ROW INDEX IN ITEM TABLE
                frappe.model.set_value(item_row.doctype, item_row.name, "item_code", frm.doc.clearance_item)
            }else{
                // CREATE NEW ROW IN ITEM TABLE
                var row = frappe.model.add_child(frm.doc, "Sales Order Item", "items");
                frappe.model.set_value(row.doctype, row.name, "item_code", frm.doc.clearance_item)
            } 
            refresh_field("items");
            
        }
        else{
            // IF CUSTOMER NOT AVAILABLE THEN THROW WARNING MESSAGE
            frm.doc.sales_order_clearances = [];
            refresh_field("sales_order_clearances");
            frappe.msgprint("Please specify: Customer. It is needed to fetch Sales Order Details.")
        }
    },
    sales_order(frm, cdt, cdn){ // EVENT TRIGGER ON SALES ORDER FIELD
        var cur_row = locals[cdt][cdn];
        var item_row = frm.doc.items[cur_row.idx - 1];
        // CHECK IF ITEM ROW IS ALREADY AVAILABLE
        if (!is_null(item_row)){
            var formatted_currency = frappe.format(cur_row.net_total, { fieldtype: "Currency", currency: frm.doc.currency });
            frappe.model.set_value(item_row.doctype, item_row.name, "start_date", cur_row.date)
            frappe.model.set_value(item_row.doctype, item_row.name, "description", `${cur_row.customer_name} - ${cur_row.quotation_label} - ${cur_row.sales_order} - ${cur_row.clearance_details} - ${$(formatted_currency).text() } `)
            frappe.model.set_value(item_row.doctype, item_row.name, "item_description_en", `${cur_row.customer_name} - ${cur_row.quotation_label} - ${cur_row.sales_order} - ${cur_row.clearance_details} - ${$(formatted_currency).text() } `)
            frappe.model.set_value(item_row.doctype, item_row.name, "item_description_de", `${cur_row.customer_name} - ${cur_row.quotation_label} - ${cur_row.sales_order} - ${cur_row.clearance_details} - ${$(formatted_currency).text() } `)
            frappe.model.set_value(item_row.doctype, item_row.name, "item_description_fr", `${cur_row.customer_name} - ${cur_row.quotation_label} - ${cur_row.sales_order} - ${cur_row.clearance_details} - ${$(formatted_currency).text() } `)
            frappe.model.set_value(item_row.doctype, item_row.name, "rate", cur_row.clearance_amount)
        }
        refresh_field("items");
    },

})

frappe.ui.form.on('Sales Order Item',{
    //
    item_name: function(frm, cdt, cdn){

		var data = frm.doc.items;
		var row = locals[cdt][cdn];
		if (data.length === 1 || data[0] === row) {
			if (frm.doc.language){
				row.item_language = frm.doc.language;
				refresh_field("item_language", cdn, "items");
			}
			
		} else {
			frm.copy_from_previous_row("items", row, ["item_language"]);
		}	
	},

	item_language: function(frm, cdt, cdn){
		
		var data = frm.doc.items;
		
		var row = locals[cdt][cdn];
		if(!(frm.doc.language=== row.item_language)){			
			let row_occurence = frm.occurence_len(data, row.item_language);
			if (row_occurence < data.length && !cur_dialog){
			
				frappe.confirm("💬"+__("  The language <b>{0}</b> in the just edited row is different to the others. Should <b>{0}</b> apply to all rows?", [ row.item_language]),
				()=>{
					frm.auto_fill_all_empty_rows(frm.doc, cdt, cdn, "items", "item_language");
				}, ()=>{
					//cancel
				})
			}
			//
		}
		else if (frm.doc.language=== row.item_language){
			
			let row_occurence = frm.occurence_len(data, row.item_language);
			if (row_occurence < data.length && !cur_dialog){
				//				
				frappe.confirm("💬"+__("    The language <b>'{0}'</b> in the just edited row is different to the others. Should <b>'{0}'</b> apply to all rows?", [ row.item_language]),
					()=>{
							frm.auto_fill_all_empty_rows(frm.doc, cdt, cdn, "items", "item_language");
						}, 
					()=>{
						//cancel
					}
				)
			}
		}
		
		
	},
})
