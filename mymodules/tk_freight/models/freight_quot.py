from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentQuotation(models.Model):
    """Freight Shipment Quotation"""
    _name = "shipment.quotation"
    _description = __doc__
    _inherit = ['portal.mixin', 'mail.thread',
                'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(copy=False, default=lambda self: _('New'))
    status = fields.Selection(
        [('q', 'Quotation'), ('qs', 'Quotation Sent'), ('c', 'Converted to Booking')], default="q")
    date = fields.Date(default=fields.Date.today())
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]))
    operation = fields.Selection(
        [('direct', 'Direct Shipment'), ('house', 'House Shipment'), ('master', 'Master Shipment')],
        string='Shipment')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'Full Container(FCL)'), ('lcl', 'Less Container(LCL)')]), string='Ocean Shipment')
    inland_shipment_type = fields.Selection(
        ([('ftl', 'Full Truckload(FTL)'), ('ltl', 'Less than Truckload(LTL)')]),
        string='Land Shipment')
    shipper_id = fields.Many2one('res.partner', domain=[('shipper', '=', True)])
    consignee_id = fields.Many2one('res.partner', domain=[('consignee', '=', True)])
    address_to = fields.Selection(
        [('sc_address', 'Contact Address'), ('location_address', 'Location Address')],
        string="Address", default="sc_address")
    order_line_ids = fields.One2many('quot.order.line', 'quot_id')
    booking_id = fields.Many2one('shipment.freight.booking', string="Booking")
    total_text = fields.Text(string="Total Amount", compute="_compute_total", translate=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    from_booking = fields.Boolean(string="From Website")
    source = fields.Char(string="Source ", translate=True)
    destination = fields.Char(translate=True)
    # GENERAL INFORMATION
    height = fields.Float(string='Height(cm)')
    width = fields.Float(string='Width(cm)')
    length = fields.Float(string='Length(cm)')
    weight = fields.Float(string='Weight(KG)')
    notes = fields.Text(translate=True)
    dangerous_goods = fields.Boolean()
    dangerous_goods_notes = fields.Text('Dangerous Goods Info', translate=True)
    # Source Address
    source_location_id = fields.Many2one('freight.port', index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')
    # Destinations Address
    destination_location_id = fields.Many2one('freight.port', index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')
    # Lead & Quotation
    lead_id = fields.Many2one('crm.lead')
    quotation_id = fields.Many2one('sale.order')

    @api.model_create_multi
    def create(self, vals_list):
        """create method"""
        for vals in vals_list:
            prefix = self.env['ir.config_parameter'].sudo().get_param('tk_freight.quot_seq')
            pre = str(prefix) if prefix else "FQ"
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = pre + self.env['ir.sequence'].next_by_code('shipment.quot') or (
                    'New')
        res = super().create(vals_list)
        return res

    @api.onchange('address_to', 'source_location_id', 'destination_location_id', 'shipper_id',
                  'consignee_id')
    def _onchange_address(self):
        """onchange address"""
        for rec in self:
            if rec.address_to in ["sc_address", "location_address"]:
                source = (
                    rec.shipper_id if rec.address_to == "sc_address" else rec.source_location_id
                )
                destination = (
                    rec.consignee_id if rec.address_to == "sc_address" else rec.destination_location_id
                )

                if source:
                    rec.s_zip = source.zip
                    rec.s_street = source.street
                    rec.s_street2 = source.street2
                    rec.s_city = source.city
                    rec.s_country_id = source.country_id.id
                    rec.s_state_id = source.state_id.id

                if destination:
                    rec.d_zip = destination.zip
                    rec.d_street = destination.street
                    rec.d_street2 = destination.street2
                    rec.d_city = destination.city
                    rec.d_country_id = destination.country_id.id
                    rec.d_state_id = destination.state_id.id

    @api.depends('order_line_ids')
    def _compute_total(self):
        """compute total"""
        for rec in self:
            currency = self.order_line_ids.mapped('currency_id').mapped('id')
            total = ""
            amount = 0.0
            for c in currency:
                currency_id = self.env['res.currency'].browse(c)
                if rec.order_line_ids:
                    for order in rec.order_line_ids:
                        if order.currency_id.id == c:
                            amount = amount + order.total_amount
                total = total + str(currency_id.name) + " " + str(amount) + "\n"
                amount = 0.0
            rec.total_text = total

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_source_destination_location(self):
        """check source and destination location"""
        for record in self:
            if record.address_to == 'location_address':
                if record.source_location_id and record.destination_location_id:
                    if record.source_location_id.id == record.destination_location_id.id:
                        if record.transport == 'air':
                            raise ValidationError(
                                _("The gateway and destination locations cannot be the same "
                                  "\nPlease change one of the locations."))
                        if record.transport == 'ocean':
                            raise ValidationError(
                                _("The loading port and discharge port cannot be the same "
                                  "\nPlease change one of the locations."))
                        if record.transport == 'land':
                            raise ValidationError(
                                _("The from and to cannot be the same \nPlease change one of the "
                                  "locations."))

    def action_convert_booking(self):
        """action convert booking"""
        if self.shipper_id and self.consignee_id:
            self.consignee_id.consignee = True
            order_lines = []
            package_line_ids = self.order_line_ids.filtered(
                lambda line: line.package_type and line.package)
            total_gross_weight = sum(package_line_ids.mapped('gross_weight'))
            total_net_weight = sum(package_line_ids.mapped('net_weight'))
            for data in self.order_line_ids:
                order_lines.append((0, 0, {
                    'service_id': data.service_id.id,
                    'currency_id': data.currency_id.id,
                    'name': data.name,
                    'sale': data.sale,
                    'qty': data.qty,
                    'tax_ids': data.tax_ids.ids,
                    'package_type': data.package_type,
                    'package': data.package.id,
                    'height': data.height,
                    'width': data.width,
                    'length': data.length,
                    'total_cbm': data.total_cbm,
                    'net_weight': data.net_weight,
                    'volume': data.volume,
                    'gross_weight': data.gross_weight,
                }))
            data = {
                'transport': self.transport,
                'operation': self.operation,
                'ocean_shipment_type': self.ocean_shipment_type,
                'inland_shipment_type': self.inland_shipment_type,
                'shipper_id': self.shipper_id.id,
                'consignee_id': self.consignee_id.id,
                'address_to': self.address_to,
                'source_location_id': self.source_location_id.id,
                'destination_location_id': self.destination_location_id.id,
                'length': self.length,
                'weight': self.weight,
                'height': self.height,
                'width': self.width,
                'notes': self.notes,
                'dangerous_goods_notes': self.dangerous_goods_notes,
                'dangerous_goods': self.dangerous_goods,
                'booking_lines_ids': order_lines,
                'total_weight': total_net_weight,
                'gross_weight': total_gross_weight,
                'no_of_containers': len(package_line_ids),
                'cargo_desc': '\n'.join(package_line_ids.mapped('package').mapped('name')),
            }
            book_id = self.env['shipment.freight.booking'].create(data)
            book_id._onchange_address()
            book_id.quot_id = self.id
            self.booking_id = book_id.id
            self.status = 'c'
            mail_template = self.env.ref('tk_freight.quot_booking_mail_template')
            if mail_template:
                mail_template.send_mail(self.id, force_send=True)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Booking',
                'res_model': 'shipment.freight.booking',
                'res_id': book_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
        message = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'title': _('Please add Shipper and Consignee to Convert Shipment !'),
                'sticky': False,
            }
        }
        return message

    def freight_quotation_sent(self):
        """freight quotation sent"""
        self.status = 'qs'
        mail_template = self.env.ref('tk_freight.quot_sent_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)


class QuotOrderLine(models.Model):
    """Shipment Order Line"""
    _name = 'quot.order.line'
    _description = __doc__

    service_id = fields.Many2one('product.product', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency')
    name = fields.Char(string='Description', required=True, translate=True)
    sale = fields.Float('Price', required=True)
    qty = fields.Float(default=1)
    quot_id = fields.Many2one('shipment.quotation', string="Shipment Quot")
    total_amount = fields.Monetary(compute="_compute_total_amount")
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    # Cargo info
    package_type = fields.Selection([('item', 'Box / Cargo'), ('container', 'Container / Box')])
    freight_package_ids = fields.Many2many('freight.package', string="Freight Packages",
                                           compute="_compute_freight_packages")
    package = fields.Many2one('freight.package', string='Size / Package',
                              domain="[('id','in',freight_package_ids)]")
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string="Net Weight (KG)")
    total_cbm = fields.Float(string="Total Volume(CBM)")
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    # Weight Ratio
    weight_ratio = fields.Float(string="Weight Divisor", compute="_compute_weight_ratio")
    chargeable_weight = fields.Float(string="Volumetric Weight",
                                     compute="_compute_chargeable_weight")
    final_weight = fields.Float(string="Chargeable Weight(KG)"
                                , compute="_compute_chargeable_weight")

    @api.depends('qty', 'sale', 'tax_ids')
    def _compute_total_amount(self):
        """compute total amount"""
        for rec in self:
            total_amount = 0.0
            tax_amount = 0.0
            if rec.sale and rec.qty:
                tax_total = sum(rec.tax_ids.mapped('amount'))
                total_amount = rec.sale * rec.qty
                tax_amount = (tax_total * total_amount) / 100
            rec.total_amount = total_amount + tax_amount

    @api.depends('package_type', 'quot_id', 'quot_id.transport')
    def _compute_freight_packages(self):
        """compute freight packages"""
        for rec in self:
            packages = []
            if rec.quot_id and rec.quot_id.transport and rec.package_type:
                domain = [
                    (rec.quot_id.transport, "=", True),
                    (rec.package_type, "=", True),
                    ("active", "=", True),
                ]
                packages = self.env["freight.package"].sudo().search(domain).ids
            rec.freight_package_ids = packages

    @api.onchange('service_id')
    def _onchange_service_description(self):
        """onchange service description"""
        for rec in self:
            if rec.service_id:
                rec.name = rec.service_id.name
                rec.sale = rec.service_id.lst_price
                rec.currency_id = self.env.company.currency_id.id

    @api.depends('weight_ratio', 'length', 'width', 'height', 'qty', 'net_weight')
    def _compute_chargeable_weight(self):
        """compute chargeable weight"""
        for rec in self:
            chargeable_weight = 0.0
            final_weight = 0.0
            if rec.weight_ratio > 0:
                chargeable_weight = (((rec.length * rec.width * rec.height) / rec.weight_ratio)
                                     * rec.qty)
            if chargeable_weight > rec.net_weight:
                final_weight = chargeable_weight
            else:
                final_weight = rec.net_weight
            rec.final_weight = final_weight
            rec.chargeable_weight = chargeable_weight

    @api.onchange('package')
    def _onchange_package_dimension(self):
        """onchange package dimension"""
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width

    @api.onchange('height', 'width', 'length')
    def onchange_package_cbm(self):
        """onchange package cbm"""
        for rec in self:
            rec.volume = (rec.height * rec.width * rec.length) / 1000000

    @api.onchange('gross_weight', 'qty')
    def onchange_package_net_weight(self):
        """onchange package net weight"""
        for rec in self:
            rec.net_weight = rec.gross_weight * rec.qty

    @api.onchange('volume', 'qty')
    def onchange_package_total_volume(self):
        """onchange package total volume"""
        for rec in self:
            rec.total_cbm = rec.volume * rec.qty

    @api.depends('quot_id', 'quot_id.transport')
    def _compute_weight_ratio(self):
        """compute weight ratio"""
        for rec in self:
            weight_ratio = 0
            ir_config = self.env['ir.config_parameter'].sudo()
            if rec.quot_id.transport == 'air':
                air = ir_config.get_param('tk_freight.air_ratio')
                weight_ratio = air if air else 0
            if rec.quot_id.transport == 'ocean':
                ocean = ir_config.get_param('tk_freight.ocean_ratio')
                weight_ratio = ocean if ocean else 0
            if rec.quot_id.transport == 'land':
                land = ir_config.get_param('tk_freight.land_ratio')
                weight_ratio = land if land else 0
            rec.weight_ratio = weight_ratio
