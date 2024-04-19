// Copyright (c) 2023, Phamos GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Software Maintenance', {
    refresh(frm) {
        $('.document-link button[data-doctype="Sales Order"]').hide();
        frm.add_custom_button('Software Maintenance', function () { 
            frappe.call({
                method: "simpatec.events.sales_order.make_sales_order",
                args: {
                    software_maintenance: frm.doc.name,
                    is_background_job: 0
                },
                callback: function (r) {
                },
            });
        }, __("Renew Sales Order"));

        frm.add_custom_button('Maintenace Order', function () { 
            let dialog = new frappe.ui.Dialog({
                title: __("Process Software Maintenance"),
                fields: [
                    {
                        fieldname: "transaction_date",
                        label: "Transaction Date",
                        fieldtype: "Date",
                    },
                ],
                primary_action(data) {
                    //let filedata = $('#upload_mac')[0].files[0];
                    if (!data || data === undefined ) {
                        frappe.throw(__("Select a new Transaction Date"));
                    } 
                    else {		
                        console.log('ask for what was clicked :',data.transaction_date,' party :', frm.doc.customer);					

                        frappe.call({
                            method: "simpatec.events.sales_order.make_maintenance_order",
                            args: {
                                data: frm.doc,
                                tran_data : data.transaction_date
                            },
                            callback: function (r) {										
                                if (r.message) {
                                    
                                }
                            },
                        });
                        
                    }							
                    //dialog.set_df_property("upload_component", "options", []);
                    dialog.hide();					
                    
                },
                primary_action_label: __('Process Software Maintenance')

        });
        
        dialog.show();
        }, __("Renew Sales Order"));

        frm.add_custom_button('Next Sales Order', function () { 
            frappe.model.open_mapped_doc({
                method: "simpatec.simpatec.doctype.software_maintenance.software_maintenance.make_sales_order",
                frm: frm
            })                
        }, __("Create"));
    }
});
