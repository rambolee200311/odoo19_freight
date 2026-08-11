# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

import datetime
from datetime import datetime, timedelta
from random import choice
from string import digits
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FreightBooking(models.Model):
    """freight bookings"""
    _name = 'shipment.freight.booking'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = __doc__

    def _get_default_stage_id(self):
        """get default stage id"""
        return self.env['freight.shipment.stages'].search([], order='sequence', limit=1)

    def _default_random_barcode(self):
        """default random barcode"""
        return "".join(choice(digits) for i in range(8))

    # Basic Details
    barcode = fields.Char(help="ID used for shipment identification.",
                          default=_default_random_barcode, copy=False)
    color = fields.Integer()
    create_datetime = fields.Datetime(string='Create Date', default=fields.Datetime.now())
    name = fields.Char(copy=False, default=lambda self: _('New'))
    direction = fields.Selection(([('import', 'Import'), ('export', 'Export')]), string='Transfer')
    state = fields.Selection(([('draft', 'Draft'), ('converted', 'Converted'),
                               ('cancel', 'Cancel')]), string='Status', default='draft')
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]))
    operation = fields.Selection([('direct', 'Direct Shipment'), ('house', 'House Shipment'),
                                  ('master', 'Master Shipment')], string='Shipment')
    ocean_shipment_type = fields.Selection(
        ([('fcl', 'Full Container(FCL)'), ('lcl', 'Less Container(LCL)')]), string='Ocean Shipment')
    inland_shipment_type = fields.Selection(
        ([('ftl', 'Full Truckload(FTL)'), ('ltl', 'Less than Truckload(LTL)')]),
        string='Land Shipment')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    freight_id = fields.Many2one('freight.shipment', 'Freight Shipment',
                                 compute="_compute_freight_id")
    address_to = fields.Selection(
        [('sc_address', 'Contact Address'), ('location_address', 'Location Address')],
        string="Address", default="sc_address")
    quot_id = fields.Many2one('shipment.quotation', string="Quotation")
    # Shipper
    shipper_id = fields.Many2one('res.partner', domain=[('shipper', '=', True)])
    shipper_email = fields.Char(related='shipper_id.email', string="Email ", translate=True)
    shipper_phone = fields.Char(related='shipper_id.phone', string="Phone ", translate=True)
    # Consignee
    consignee_id = fields.Many2one('res.partner', domain=[('consignee', '=', True)])
    consignee_email = fields.Char(related='consignee_id.email', translate=True)
    consignee_phone = fields.Char(related='consignee_id.phone', translate=True)
    # Cancellation Reason
    cancellation_reason_head = fields.Char(string="Cancellation Reason", translate=True)
    cancellation_reason = fields.Text(string="Cancellation", translate=True)
    # Datetime/Common Field
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    # Ocean
    obl = fields.Char('OBL No.', help='Original Bill Of Landing', translate=True)
    voyage_no = fields.Char(translate=True)
    vessel_id = fields.Many2one('freight.vessel', string='Vessel/Ship')
    ship_owner_id = fields.Many2one(related='vessel_id.owner_id', string="Shipping Line")
    # Land
    truck_ref = fields.Char('CMR/RWB', translate=True)
    trucker = fields.Many2one('fleet.vehicle', 'Vehicle')
    trucker_number = fields.Char('Reference', translate=True)
    truck_owner_id = fields.Many2one(related="trucker.owner_id", string="Owner")
    # Air
    mawb_no = fields.Char('MAWB No', translate=True)
    airline_id = fields.Many2one('freight.airline')
    flight_no = fields.Char(translate=True)
    airline_owner_id = fields.Many2one(related="airline_id.owner_id", string="Airline Owner")

    # General Information
    agent_id = fields.Many2one('res.partner', domain=[('agent', '=', True)])
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                                  string='Responsible', required=True)
    notes = fields.Text(translate=True)
    dangerous_goods = fields.Boolean()
    dangerous_goods_notes = fields.Text('Dangerous Goods Info', translate=True)
    move_type = fields.Many2one('freight.move.type')
    tracking_number = fields.Char(translate=True)
    incoterm = fields.Many2one('freight.incoterms')
    # Notify Party
    first_notify_id = fields.Many2one('res.partner', string="1st Notify",
                                      domain="[('notify','=',True)]")
    second_notify_id = fields.Many2one('res.partner', string="2nd Notify",
                                       domain="[('notify','=',True)]")
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
    # Final Destination
    final_destination_id = fields.Many2one('freight.port', string="Final Destination")
    # Booking Report Fields
    cargo_desc = fields.Text(string="Cargo Description", translate=True)
    hs_code = fields.Char(string="HS Code", translate=True)
    no_of_containers = fields.Integer()
    container_size = fields.Many2one('freight.package', string="Container Type")
    total_weight = fields.Char(translate=True)
    gross_weight = fields.Char(translate=True)
    container_type = fields.Selection(
        [('dry', 'Dry'), ('reefer', 'Reefer'), ('flat_rock', 'Flat Rock'), ('open_top', 'Open Top'),
         ('other', 'Other')], string="Container Type ")
    other_container_type = fields.Char(string="Container Type  ", translate=True)
    temperature = fields.Char(translate=True)
    humidity = fields.Char(translate=True)
    ventilation = fields.Char(translate=True)
    mask_numbers = fields.Text(string="Mask & Numbers", translate=True)
    commodity = fields.Text(translate=True)
    bl_document_type = fields.Selection(
        [('Draft', 'DRAFT'), ('Copy', 'COPY NON NEGOTIABLE '), ('original', 'ORIGINAL'),
         ('telex_release', 'Telex Release')], string="B/L Document Type")
    freight_collect_prepaid = fields.Selection([('Collect', 'Collect'), ('Prepaid', 'Prepaid')],
                                               string="Bill", default="Collect")
    # Booking Line From Quotation
    booking_lines_ids = fields.One2many('booking.order.line', 'booking_id')
    # DEPRECATED FIELDS
    approx_charges = fields.Monetary()
    distance = fields.Integer()
    height = fields.Float()
    width = fields.Float()
    length = fields.Float()
    weight = fields.Float()
    declaration_number = fields.Char()
    declaration_date = fields.Date()
    custom_clearnce_date = fields.Datetime()
    book_vals = fields.Char()
    attachment = fields.Many2many('ir.attachment', 'attach_booking_rel', 'doc_id', 'booking_id',
                                  help='You can attach the copy of your document', copy=False)
    track_ids = fields.One2many('booking.line', 'booking_id', 'Tracker Lines')

    @api.model_create_multi
    def create(self, vals_list):
        """create method"""
        for vals in vals_list:
            prefix = self.env['ir.config_parameter'].sudo(
            ).get_param('tk_freight.booking_seq')
            pre = str(prefix) if prefix else "BOOKING"
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = pre + self.env['ir.sequence'].next_by_code(
                    'shipment.freight.booking') or _('New')
            vals['tracking_number'] = vals.get('name')
        res = super().create(vals_list)
        return res

    # Constrains
    @api.constrains('source_location_id', 'destination_location_id')
    def _check_source_destination_location(self):
        """check source destination location"""
        for record in self:
            if (record.address_to == 'location_address' and record.source_location_id
                    and record.destination_location_id
                    and record.source_location_id.id == record.destination_location_id.id):
                raise ValidationError(_(
                    "The source and destination locations cannot be the same !\nplease "
                    "change one of the locations."))

    @api.constrains('first_notify_id', 'second_notify_id')
    def _check_notify_party(self):
        """check a notify party"""
        for rec in self:
            if (rec.first_notify_id and rec.second_notify_id
                    and rec.first_notify_id.id == rec.second_notify_id.id):
                raise ValidationError(
                    _("Please change one of the notify party as both parties cannot be the same."))

    @api.constrains('create_datetime', 'pickup_datetime', 'arrival_datetime')
    def _check_pickup_datetime(self):
        """check pickup date time"""
        for rec in self:
            if (rec.create_datetime and rec.pickup_datetime
                    and rec.pickup_datetime < rec.create_datetime):
                raise ValidationError(_("Estimate pickup time cannot be earlier than create date."))
            if (rec.arrival_datetime and rec.pickup_datetime
                    and rec.arrival_datetime < rec.pickup_datetime):
                raise ValidationError(
                    _("Estimate arrival time cannot be earlier than estimate pickup time."))
            if (rec.arrival_datetime and rec.create_datetime
                    and rec.arrival_datetime < rec.create_datetime):
                raise ValidationError(
                    _("Estimate arrival time cannot be earlier than create date."))

    def convert_to_operation(self):
        """convert to operation"""
        if self.address_to and self.address_to == 'location_address':
            if not self.source_location_id:
                raise ValidationError(_("Please select gateway in location details."))
            if not self.destination_location_id:
                raise ValidationError(_("Please select destination in location details."))
        if not self.shipper_id or not self.consignee_id:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _('Please add shipper and consignee to convert shipment !'),
                    'sticky': False,
                }
            }
            return message
        self.state = "converted"
        data = {
            'operation': self.operation,
            'direction': self.direction,
            'transport': self.transport,
            'ocean_shipment_type': self.ocean_shipment_type,
            'inland_shipment_type': self.inland_shipment_type,
            'shipper_id': self.shipper_id.id,
            'consignee_id': self.consignee_id.id,
            'source_location_id': self.source_location_id.id,
            'destination_location_id': self.destination_location_id.id,
            'mawb_no': self.mawb_no,
            'flight_no': self.flight_no,
            'airline_id': self.airline_id.id,
            'vessel_id': self.vessel_id.id,
            'voyage_no': self.voyage_no,
            'obl': self.obl,
            'truck_ref': self.truck_ref,
            'trucker_number': self.trucker_number,
            'trucker': self.trucker.id,
            'barcode': self.barcode,
            'notes': self.notes,
            'dangerous_goods': self.dangerous_goods,
            'dangerous_goods_notes': self.dangerous_goods_notes,
            'agent_id': self.agent_id.id,
            'operator_id': self.operator_id.id,
            'move_type': self.move_type.id,
            'incoterm': self.incoterm.id,
            'pickup_datetime': self.pickup_datetime,
            'arrival_datetime': self.arrival_datetime,
            'distance': self.distance,
            'address_to': self.address_to,
            'final_destination_id': self.final_destination_id.id,
            'second_notify_id': self.second_notify_id.id,
            'first_notify_id': self.first_notify_id.id,
            'quotation_id': self.quot_id.id,
        }
        booking_id = self.env['freight.shipment'].sudo().create(data)
        booking_id.booking_id = self.id
        booking_id._onchange_address()
        for data in self.booking_lines_ids:
            if data.package_type and data.package:
                self.env['shipment.package.line'].create({
                    'package_type': data.package_type,
                    'package': data.package.id,
                    'gross_weight': data.gross_weight,
                    'net_weight': data.net_weight,
                    'height': data.height,
                    'length': data.length,
                    'charges': data.sale,
                    'width': data.width,
                    'volume': data.volume,
                    'total_cbm': data.total_cbm,
                    'qty': data.qty,
                    'shipment_id': booking_id.id,
                    'line_added': True,
                })
            self.env['freight.service'].create({
                'service_type': 'consignee',
                'consignee_id': self.consignee_id.id,
                'service_id': data.service_id.id,
                'name': data.name,
                'qty': data.qty,
                'currency_id': data.currency_id.id,
                'sale': data.sale,
                'shipment_id': booking_id.id
            })

        mail_template = self.env.ref('tk_freight.booking_shipment_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Shipment',
            'res_model': 'freight.shipment',
            'res_id': booking_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def convert_to_cancel(self):
        """convert to cancel"""
        for rec in self:
            rec.state = 'cancel'

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

    def _compute_freight_id(self):
        """compute freight id"""
        for rec in self:
            rec.freight_id = (self.env['freight.shipment'].search(
                [('booking_id', '=', self.id)], limit=1)).id


class BookingOrderLine(models.Model):
    """Booking Order Line"""
    _name = 'booking.order.line'
    _description = __doc__

    service_id = fields.Many2one('product.product', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency')
    name = fields.Char(string='Description', required=True, translate=True)
    sale = fields.Float('Price', required=True)
    qty = fields.Float(default=1)
    booking_id = fields.Many2one('shipment.freight.booking')
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
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    total_cbm = fields.Float(string="Total Volume(CBM)")
    # Weight Ratio
    weight_ratio = fields.Float(compute="_compute_weight_ratio")
    chargeable_weight = fields.Float(compute="_compute_chargeable_weight")

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

    @api.depends('package_type', 'booking_id', 'booking_id.transport')
    def _compute_freight_packages(self):
        """compute freight packages"""
        for rec in self:
            packages = []
            if rec.booking_id and rec.booking_id.transport and rec.package_type:
                domain = [
                    (rec.booking_id.transport, "=", True),
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

    @api.depends('weight_ratio', 'length', 'width', 'height', 'qty')
    def _compute_chargeable_weight(self):
        """compute chargeable weight"""
        for rec in self:
            chargeable_weight = 0.0
            if rec.weight_ratio > 0:
                chargeable_weight = (((rec.length * rec.width * rec.height) / rec.weight_ratio)
                                     * rec.qty)
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

    @api.depends('booking_id', 'booking_id.transport')
    def _compute_weight_ratio(self):
        """compute a weight ratio"""
        for rec in self:
            weight_ratio = 0
            ir_config = self.env['ir.config_parameter'].sudo()
            if rec.booking_id.transport == 'air':
                air = ir_config.get_param('tk_freight.air_ratio')
                weight_ratio = air if air else 0
            if rec.booking_id.transport == 'ocean':
                ocean = ir_config.get_param('tk_freight.ocean_ratio')
                weight_ratio = ocean if ocean else 0
            if rec.booking_id.transport == 'land':
                land = ir_config.get_param('tk_freight.land_ratio')
                weight_ratio = land if land else 0
            rec.weight_ratio = weight_ratio


# DEPRECATED MODEL
class BookingLine(models.Model):
    """Booking Line"""
    _name = 'booking.line'
    _description = __doc__

    name = fields.Char('Note', translate=True)
    user_id = fields.Many2one('res.users', 'User ID')
    date = fields.Datetime()
    actual_date = fields.Datetime('Actual')
    vendor_attachment = fields.Binary(attachment=True, string="Attachment")
    booking_id = fields.Many2one('shipment.freight.booking', 'Tender')

    @api.depends('date')
    def compute_actual(self):
        """compute actual"""
        for line in self:
            line.actual_date = datetime.strptime(
                str(line.create_date), "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)
