from odoo import fields, models, _


class FreightCRM(models.Model):
    """freight crm"""
    _inherit = 'crm.lead'

    quotation_id = fields.Many2one('sale.order', string="Quotation",
                                   domain="[('opportunity_id','=',id)]") # deprecated
    freight_quotation_id = fields.Many2one('shipment.quotation', string="Freight Quotation")

    # Carriage Details
    source = fields.Char(string="Source ", translate=True)
    destination = fields.Char(translate=True)
    height = fields.Float(string='Height(cm)')
    width = fields.Float(string='Width(cm)')
    length = fields.Float(string='Length(cm)')
    weight = fields.Float(string='weight(KG)')
    dangerous_goods = fields.Boolean()
    freight_note = fields.Text(string="Notes ")
    dangerous_goods_notes = fields.Text('Dangerous Goods Info', translate=True)

    def action_create_freight_quotation(self):
        """action create fright quotation"""
        freight_quotation_id = self.env['shipment.quotation'].create({
            'lead_id': self.id,
            'source': self.source,
            'consignee_id': self.partner_id.id,
            'destination': self.destination,
            'height': self.height,
            'width': self.width,
            'length': self.length,
            'weight': self.weight,
            'dangerous_goods': self.dangerous_goods,
            'notes': self.freight_note,
            'dangerous_goods_notes': self.dangerous_goods_notes,
        })
        freight_quotation_id._onchange_address()
        self.freight_quotation_id = freight_quotation_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Freight Quotation',
            'res_model': 'shipment.quotation',
            'res_id': freight_quotation_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
