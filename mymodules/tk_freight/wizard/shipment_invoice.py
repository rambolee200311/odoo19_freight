from odoo import fields, _, models


class ShipmentInvoice(models.TransientModel):
    """Shipment Invoice to Shipper or Consignee"""
    _name = "shipment.invoice"
    _description = __doc__

    invoice_to = fields.Selection([('shipper', 'Shipper'), ('consignee', 'Consignee')])
    shipment_id = fields.Many2one('freight.shipment', string="Shipment")

    def action_create_invoice(self):
        """action create invoice"""
        for rec in self:
            sale_order = True
            for record in rec.shipment_id.freight_services:
                if record.service_type == 'customer' and not record.sale_order_id:
                    sale_order = False
            if sale_order:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': _('No New Service Add for Shipper / Consignee'),
                        'sticky': False,
                    }
                }
                return message

            if rec.shipment_id and rec.shipment_id.total_service_charge <= 0:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'message': _("Service Charge cannot be zero or negative"),
                        'sticky': False,
                    }
                }
                return message

            if rec.invoice_to == "consignee":
                invoice_lines = []
                for service in rec.shipment_id.freight_services:
                    if not service.sale_order_id and service.service_type == 'customer':
                        service.status = 'quotation'
                        record = {
                            'product_id': service.service_id.id,
                            'name': service.name,
                            'product_uom_qty': service.qty,
                            'price_unit': service.sale,
                        }
                        invoice_lines.append((0, 0, record))
                data = {
                    'partner_id': rec.shipment_id.consignee_id.id,
                    'order_line': invoice_lines,
                    'freight_id': rec.shipment_id.id
                }
                sale_order_id = self.env['sale.order'].create(data)
                for service in rec.shipment_id.freight_services:
                    if service.service_type == 'customer' and not service.sale_order_id:
                        service.sale_order_id = sale_order_id.id

                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Sale Order'),
                    'res_model': 'sale.order',
                    'res_id': sale_order_id.id,
                    'view_mode': 'form',
                    'target': 'current'
                }

            if rec.invoice_to == "shipper":
                invoice_lines = []
                for service in rec.shipment_id.freight_services:
                    if not service.sale_order_id and service.service_type == 'customer':
                        service.status = 'quotation'
                        record = {
                            'product_id': service.service_id.id,
                            'name': service.name,
                            'product_uom_qty': service.qty,
                            'price_unit': service.sale,
                        }
                        invoice_lines.append((0, 0, record))
                data = {
                    'partner_id': rec.shipment_id.shipper_id.id,
                    'order_line': invoice_lines,
                    'freight_id': rec.shipment_id.id
                }
                sale_order_id = self.env['sale.order'].create(data)
                for service in rec.shipment_id.freight_services:
                    if service.service_type == 'customer' and not service.sale_order_id:
                        service.sale_order_id = sale_order_id.id
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Sale Order'),
                    'res_model': 'sale.order',
                    'res_id': sale_order_id.id,
                    'view_mode': 'form',
                    'target': 'current'
                }
        return True
