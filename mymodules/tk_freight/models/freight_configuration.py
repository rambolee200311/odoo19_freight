import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """res partner"""
    _inherit = 'res.partner'

    shipper = fields.Boolean()
    consignee = fields.Boolean()
    agent = fields.Boolean()
    is_policy = fields.Boolean('Policy Company')
    vendor = fields.Boolean()
    notify = fields.Boolean()
    multiple_invoice_ids = fields.One2many('freight.multiple.invoice', 'partner_id')


class ProductTemplate(models.Model):
    """Product tax master data used by settlement statements."""
    _inherit = 'product.template'

    tax_code = fields.Char(string='Tax Code')
    tax_name = fields.Char(string='Tax Name')


class CustomerInvoice(models.Model):
    """customer invoice"""
    _inherit = 'account.move'

    freight_operation_id = fields.Many2one('freight.shipment', string='Freight Shipment')
    freight_statement_id = fields.Many2one('freight.statement', string='Freight Statement')
    direction = fields.Selection(related="freight_operation_id.direction", string='Direction')
    transport = fields.Selection(related="freight_operation_id.transport", string='Transport Via')
    operation = fields.Selection(related="freight_operation_id.operation", string='Operation')
    shipper_id = fields.Many2one(related="freight_operation_id.shipper_id", string="Shipper")
    consignee_id = fields.Many2one(related="freight_operation_id.consignee_id", string="Consignee")
    agent_id = fields.Many2one(related="freight_operation_id.agent_id", string="Agent")
    source_location_id = fields.Many2one(related="freight_operation_id.source_location_id",
                                         string='Source Location')
    destination_location_id = fields.Many2one(related="freight_operation_id.source_location_id",
                                              string='Destination Location')

    @api.onchange('freight_operation_id')
    def _onchange_freight_operation_id(self):
        """onchange freight operation id"""
        for rec in self:
            if rec.freight_operation_id:
                if rec.move_type == 'out_invoice':
                    rec.partner_id = rec.freight_operation_id.consignee_id.id
                if rec.move_type == 'in_invoice':
                    rec.partner_id = rec.freight_operation_id.agent_id.id


class CustomDepartment(models.Model):
    """Custom Department Services"""
    _name = 'custom.department'
    _description = __doc__

    freight_id = fields.Many2one('freight.shipment')
    declaration = fields.Char('Declaration No.', translate=True)
    note = fields.Char(translate=True)
    date = fields.Date()
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(translate=True)
    state = fields.Selection([('pass', 'Pass'), ('in_process', 'Processing'), ('cancel', 'Cancel')],
                             string='Status')

    def action_pass(self):
        """action pass"""
        for rec in self:
            rec.state = 'pass'

    def action_in_process(self):
        """action in process"""
        for rec in self:
            rec.state = 'in_process'

    def action_cancel(self):
        """action cancel"""
        for rec in self:
            rec.state = 'cancel'


class ShipmentStages(models.Model):
    """shipment Stage"""
    _name = 'freight.shipment.stages'
    _description = __doc__
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    is_last_stage = fields.Boolean()

    @api.constrains('is_last_stage')
    def _check_is_last_stage(self):
        """check last stage"""
        for rec in self:
            last_stages = self.search([('id', '!=', rec.id)])
            for stage in last_stages:
                if stage.is_last_stage:
                    raise ValidationError(_("Last stage is already assigned to %s", stage.name))


class ShipmentTracking(models.Model):
    """Shipment Tracking"""
    _name = 'shipment.tracking'
    _description = __doc__

    date = fields.Date(required=True)
    time = fields.Float()
    location_id = fields.Many2one('shipment.location', string="Location ", required=True)
    activity_id = fields.Many2one('shipment.location.activity')
    shipment_id = fields.Many2one('freight.shipment', string='Shipment ID')
    status = fields.Selection([('pending', 'Pending'), ('complete', 'Complete')], default="pending")

    @api.model_create_multi
    def create(self, vals_list):
        """create method"""
        for shipment in vals_list:
            if not shipment['date']:
                raise ValidationError(_("Inside shipment tracking. \nInvalid field date."))
            if not shipment['location_id']:
                raise ValidationError(_("Inside shipment tracking. \nInvalid field location."))
        return super().create(vals_list)

    @api.constrains('time')
    def _check_time(self):
        """check time"""
        for rec in self:
            if rec.time >= 25:
                raise ValidationError(
                    _("In shipment tracking time cannot be greater than 24 hours"))

    @api.constrains('date')
    def _check_date(self):
        """check date"""
        for rec in self:
            if rec.date:
                next_shipment = self.search(
                    [('id', '!=', rec.id), ('shipment_id', '=', rec.shipment_id.id),
                     ('date', '!=', False),
                     ('id', ">", rec.id)], order="create_date", limit=1)

                previous_shipments = self.search(
                    [('id', '!=', rec.id), ('shipment_id', '=', rec.shipment_id.id),
                     ('date', '!=', False),
                     ('id', "<", rec.id)], order="create_date DESC")

                previous_shipment_id = 0
                for shipment in previous_shipments:
                    if previous_shipment_id < shipment.id:
                        previous_shipment_id = shipment.id
                previous_shipment = self.search(
                    [('id', '=', previous_shipment_id), ('shipment_id', '=', rec.shipment_id.id),
                     ('date', '!=', False)])

                if previous_shipment and rec.date < previous_shipment.date:
                    raise ValidationError(
                        _("In shipment tracking shipment date cannot be earlier than previous "
                          "shipments date."))
                if next_shipment and rec.date > next_shipment.date:
                    raise ValidationError(
                        _("In shipment tracking shipment date cannot be after than next shipments "
                          "date."))

    def action_complete(self):
        """action complete"""
        self.status = "complete"


class SaleOrder(models.Model):
    """sale order"""
    _inherit = 'sale.order'

    freight_id = fields.Many2one('freight.shipment')
    direction = fields.Selection(related="freight_id.direction", string='Direction')
    transport = fields.Selection(related="freight_id.transport", string='Transport Via')
    operation = fields.Selection(related="freight_id.operation", string='Operation')
    shipper_id = fields.Many2one(related="freight_id.shipper_id", string="Shipper")
    consignee_id = fields.Many2one(related="freight_id.consignee_id", string="Consignee")
    agent_id = fields.Many2one(related="freight_id.agent_id", string="Agent")
    source_location_id = fields.Many2one(related="freight_id.source_location_id",
                                         string='Source Location')
    destination_location_id = fields.Many2one(related="freight_id.source_location_id",
                                              string='Destination Location')


class ShipmentPackageLine(models.Model):
    """Freight Package Line"""
    _name = 'shipment.package.line'
    _description = __doc__
    _rec_name = 'package'

    name = fields.Char(string='Container Number', translate=True)
    package_type = fields.Selection([('item', 'Box / Cargo'), ('container', 'Container / Box')])
    transport = fields.Selection(([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')]))
    shipment_id = fields.Many2one('freight.shipment', 'Shipment ID')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    freight_package_ids = fields.Many2many('freight.package', string="Freight Packages",
                                           compute="_compute_freight_packages")
    package = fields.Many2one('freight.package', string='Size / Package',
                              domain="[('id','in',freight_package_ids)]")
    charges = fields.Monetary()
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer'), ('flat_rock', 'Flat Rock'),
                              ('open_top', 'Open Top'), ('other', 'Other')]), string="Type ")
    qty = fields.Float(required=True, default=1.0)
    harmonize = fields.Char(translate=True)
    temperature = fields.Char(translate=True)
    humidity = fields.Char(translate=True)
    ventilation = fields.Char(translate=True)
    vgm = fields.Char('VGM', help='Verified gross mass', translate=True)
    carrier_seal = fields.Char(translate=True)
    seal_number = fields.Char(translate=True)
    reference = fields.Char(translate=True)
    dangerous_goods = fields.Boolean()
    class_number = fields.Char(translate=True)
    un_number = fields.Char('UN Number', translate=True, size=4)
    Package_group = fields.Char('Packaging Group', translate=True)
    imdg_code = fields.Char('IMDG Code', help='International Maritime Dangerous Goods Code',
                            translate=True)
    flash_point = fields.Char(translate=True)
    material_description = fields.Text(translate=True)
    freight_item_lines = fields.One2many('shipment.item', 'package_line_id')
    route_id = fields.Many2one('freight.route')
    container_type = fields.Selection(
        [('GP', 'GP (General Purpose)'), ('HC', 'HC (High Cube)'), ('RF', 'RF (Reefer)'),
         ('FR', 'FR (Flat Rack)'), ('OT', 'OT (Open Top)'), ('GOH', 'GOH (Garment of Hanger)')],
        default="GP")
    cargo_type = fields.Selection([('stackable', 'Stackable'), ('non_stackable', 'Non Stackable')])
    # Dimension
    volume = fields.Float('Volume (CBM)')
    total_cbm = fields.Float(string="Total Volume(CBM)")
    gross_weight = fields.Float('Gross Weight (KG)')
    net_weight = fields.Float(string="Net Weight (KG)")
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    # line added
    line_added = fields.Boolean()
    # Weight Ratio
    weight_ratio = fields.Float(compute="_compute_weight_ratio")
    chargeable_weight = fields.Float(string="Volumetric Weight",
                                     compute="_compute_chargeable_weight")
    final_weight = fields.Float(string="Chargeable Weight(KG)",
                                compute="_compute_chargeable_weight")

    @api.depends('shipment_id', 'shipment_id.transport')
    def _compute_weight_ratio(self):
        """compute weight ratio"""
        for rec in self:
            weight_ratio = 0
            ir_config = self.env['ir.config_parameter'].sudo()
            if rec.shipment_id.transport == 'air':
                air = ir_config.get_param('tk_freight.air_ratio')
                weight_ratio = air if air else 0
            if rec.shipment_id.transport == 'ocean':
                ocean = ir_config.get_param('tk_freight.ocean_ratio')
                weight_ratio = ocean if ocean else 0
            if rec.shipment_id.transport == 'land':
                land = ir_config.get_param('tk_freight.land_ratio')
                weight_ratio = land if land else 0
            rec.weight_ratio = weight_ratio

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

    @api.onchange('package_type')
    def _onchange_package_type(self):
        """onchange package type"""
        for rec in self:
            rec.package = False

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
                rec.charges = rec.package.charge

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

    @api.depends('package_type', 'shipment_id', 'shipment_id.transport')
    def _compute_freight_packages(self):
        """compute freight packages"""
        for rec in self:
            packages = []
            if rec.shipment_id and rec.shipment_id.transport and rec.package_type:
                domain = [
                    (rec.shipment_id.transport, "=", True),
                    (rec.package_type, "=", True),
                    ("active", "=", True),
                ]
                packages = self.env["freight.package"].sudo().search(domain).ids
            rec.freight_package_ids = packages

    @api.constrains('un_number')
    def _check_un_number(self):
        """check un number"""
        for rec in self:
            un_number = None
            try:
                un_number = int(rec.un_number)
            except Exception as e:
                _logger.warning(e)
            if rec.dangerous_goods and rec.un_number and not un_number:
                raise ValidationError(_("In package details tab UN Number contains only digits."))

    def action_insert_line_service(self):
        """action insert line service"""
        if not self.charges > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': (_('Charges should be greater than zero !')),
                    'next': {'type': 'ir.actions.act_window_close'},
                    'sticky': False,
                }
            }
        desc = "Box / Cargo" if self.package_type == "item" else "Container / Box"
        self.env['freight.service'].create(
            {'service_id': self.env.ref('tk_freight.charges_product_1').id,
             'name': desc + " Charges " + "\n" + "Container No : " + str(self.name),
             'qty': 1.0,
             'sale': self.charges,
             'cost': self.charges,
             'currency_id': self.env.company.currency_id.id,
             'shipment_id': self.shipment_id.id})
        self.line_added = True
        return True


class ShipmentItem(models.Model):
    """Shipment Item Line"""
    _name = 'shipment.item'
    _description = __doc__

    name = fields.Char(string='Description', translate=True)
    package_line_id = fields.Many2one('shipment.package.line', 'Shipment ID')
    freight_package_ids = fields.Many2many('freight.package', compute="_compute_freight_package")
    package = fields.Many2one('freight.package', 'Item', domain="[('id','in',freight_package_ids)]")
    type = fields.Selection(([('dry', 'Dry'), ('reefer', 'Reefer')]), string="Operation")
    qty = fields.Float(default=1.0)
    # Dimension
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')

    @api.depends('package_line_id', 'package_line_id.shipment_id.transport')
    def _compute_freight_package(self):
        """compute freight package"""
        for line in self:
            ids = []
            freight_package = self.env['freight.package'].sudo()
            if line.package_line_id.shipment_id.transport == 'air':
                ids = freight_package.search(
                    [('air', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            if line.package_line_id.shipment_id.transport == 'ocean':
                ids = freight_package.search(
                    [('ocean', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            if line.package_line_id.shipment_id.transport == 'land':
                ids = freight_package.search(
                    [('land', '=', True), ('item', '=', True), ('active', '=', True)]).mapped('id')
            line.freight_package_ids = ids

    @api.onchange('package')
    def _onchange_item_dimension(self):
        """onchange item dimension"""
        for rec in self:
            if rec.package:
                rec.volume = rec.package.volume
                rec.gross_weight = rec.package.gross_weight
                rec.height = rec.package.height
                rec.length = rec.package.length
                rec.width = rec.package.width
                rec.name = rec.package.desc


class FreightService(models.Model):
    """Freight Service"""
    _name = 'freight.service'
    _description = __doc__

    shipment_id = fields.Many2one('freight.shipment')
    route_id = fields.Many2one('freight.route')
    # Services
    service_type = fields.Selection(
        [('shipper', 'Shipper'), ('consignee', 'Consignee'), ('vendor', 'Vendor')],
        default="shipper", string="Service To")
    service_id = fields.Many2one('product.product', domain="[('type','=','service')]")
    currency_id = fields.Many2one('res.currency')
    name = fields.Char(string='Description', required=True, translate=True)
    cost = fields.Float()
    sale = fields.Float('Price', required=True)
    qty = fields.Float(default=1)
    status = fields.Selection([('bill', 'Bill Created'), ('invoice', 'Invoice Created'),
                               ('pending', 'Pending')], default="pending", readonly=True)
    # Invoice
    shipper_id = fields.Many2one('res.partner', domain="[('shipper','=',True)]")
    consignee_id = fields.Many2one('res.partner', domain="[('consignee','=',True)]")
    customer_invoice = fields.Many2one('account.move')
    invoiced = fields.Boolean()
    # Bill
    vendor = fields.Selection([('single', 'Single Vendor'), ('multiple', 'Multiple Vendor')],
                              string='Vendor ', store=True)
    vendor_id = fields.Many2one('res.partner',
                                domain="['|',('notify','=',True),('vendor','=',True)]")
    vendor_invoice = fields.Many2one('account.move')
    vendor_invoiced = fields.Boolean()
    sale_order_id = fields.Many2one('sale.order')
    # Statement partial lock (B-52): fees inside confirmed/draft_invoice statements
    statement_line_ids = fields.One2many('freight.statement.line', 'freight_service_id',
                                         string='Statement Lines')
    statement_locked = fields.Boolean(string='Statement Locked',
                                      compute='_compute_statement_locked')

    @api.depends('statement_line_ids.statement_id.state')
    def _compute_statement_locked(self):
        for rec in self:
            rec.statement_locked = any(
                line.statement_id.state in ('confirmed', 'draft_invoice')
                for line in rec.statement_line_ids)

    def write(self, vals):
        if self.filtered('statement_locked'):
            raise ValidationError(_(
                'Fees included in a confirmed statement cannot be modified. '
                'Void the statement or use a new version.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered('statement_locked'):
            raise ValidationError(_(
                'Fees included in a confirmed statement cannot be deleted.'))
        return super().unlink()

    @api.model
    def default_get(self, fields_list):
        """default get"""
        res = super().default_get(fields_list)
        shipper_id = self.env.context.get('shipper_id')
        consignee_id = self.env.context.get('consignee_id')
        if shipper_id:
            res['shipper_id'] = shipper_id
        if consignee_id:
            res['consignee_id'] = consignee_id
        return res

    @api.onchange('service_id')
    def _onchange_service_description(self):
        """onchange service description"""
        for rec in self:
            if rec.service_id:
                rec.name = rec.service_id.name
                rec.currency_id = self.env.company.currency_id.id
                rec.sale = rec.service_id.lst_price


class FreightRoute(models.Model):
    """Freight Route"""
    _name = 'freight.route'
    _description = __doc__

    sequence = fields.Integer()
    name = fields.Char('Route', compute='_compute_name', translate=True)
    type = fields.Selection(
        [('pickup', 'Pickup'), ('oncarriage', 'On Carriage'), ('precarriage', 'Pre Carriage'),
         ('delivery', 'Delivery')], default='pickup')
    shipment_id = fields.Many2one('freight.shipment')
    transport = fields.Selection([('air', 'Air'), ('ocean', 'Ocean'), ('land', 'Land')])
    ocean_shipment_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')])
    inland_shipment_type = fields.Selection([('ftl', 'FTL'), ('ltl', 'LTL')])
    freight_services = fields.One2many('freight.service', 'route_id')
    main_carriage = fields.Boolean()
    shipper_id = fields.Many2one('res.partner', domain=[('shipper', '=', True)])
    consignee_id = fields.Many2one('res.partner', domain=[('consignee', '=', True)])
    charge_type = fields.Selection([('f', 'Free'), ('p', 'Paid')])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    total_charge = fields.Monetary(string="Charges")
    address_to = fields.Selection(
        [('sc_address', 'Contact Address'), ('location_address', 'Location Address')],
        string="Address", default="sc_address")
    # Datetime/Common Field
    pickup_datetime = fields.Datetime('Estimate Pickup Time')
    arrival_datetime = fields.Datetime('Estimate Arrival Time')
    final_charges = fields.Monetary(string='Total Charges')

    # Source Address
    source_location = fields.Char(string="Source", translate=True)
    source_location_id = fields.Many2one('freight.port', index=True)
    s_zip = fields.Char()
    s_street = fields.Char(translate=True)
    s_street2 = fields.Char(translate=True)
    s_city = fields.Char(translate=True)
    s_country_id = fields.Many2one('res.country')
    s_state_id = fields.Many2one('res.country.state')
    # Destinations Address
    destination_location = fields.Char(string="Destination", translate=True)
    destination_location_id = fields.Many2one('freight.port', index=True)
    d_zip = fields.Char()
    d_street = fields.Char(translate=True)
    d_street2 = fields.Char(translate=True)
    d_city = fields.Char(translate=True)
    d_country_id = fields.Many2one('res.country')
    d_state_id = fields.Many2one('res.country.state')
    # Ocean
    obl = fields.Char('OBL No.', help='Original Bill Of Landing', translate=True)
    voyage_no = fields.Char(translate=True)
    vessel_id = fields.Many2one('freight.vessel')
    # Air
    mawb_no = fields.Char('MAWB No', translate=True)
    airline_id = fields.Many2one('freight.airline')
    flight_no = fields.Char(translate=True)
    # Land
    truck_ref = fields.Char('CMR/RWB#/PRO#:', translate=True)
    trucker = fields.Many2one('fleet.vehicle')
    trucker_number = fields.Char(string='Reference', translate=True)
    # Line Added
    line_added = fields.Boolean()
    # Delivery Orders
    delivery_order_id = fields.Many2one('stock.picking')
    pickup_from_warehouse = fields.Boolean()
    delivery_to_warehouse = fields.Boolean()
    internal_transfer = fields.Boolean()
    partner_id = fields.Many2one('res.partner', 'Contact')
    source_warehouse_id = fields.Many2one('stock.warehouse')
    destination_warehouse_id = fields.Many2one('stock.warehouse')

    @api.model_create_multi
    def create(self, vals_list):
        """create method"""
        res = super().create(vals_list)
        for rec in res:
            rec.freight_services.write({'shipment_id': rec.shipment_id.id})
        return res

    def write(self, vals):
        """write method"""
        res = super().write(vals)
        self.freight_services.write({'shipment_id': self.shipment_id.id})
        return res

    def default_get(self, fields_list):
        """default get"""
        res = super().default_get(fields_list)
        shipper_id = self.env.context.get('shipper_id')
        consignee_id = self.env.context.get('consignee_id')
        if shipper_id:
            res['shipper_id'] = shipper_id
        if consignee_id:
            res['consignee_id'] = consignee_id
        return res

    @api.onchange('type')
    def _onchange_type(self):
        """ Onchange Route Type """
        for rec in self:
            rec.delivery_to_warehouse = False
            rec.internal_transfer = False
            rec.pickup_from_warehouse = False

    @api.onchange('pickup_from_warehouse', 'delivery_to_warehouse', 'internal_transfer')
    def _onchange_warehouse_booleans(self):
        """ Onchange Warehouse Booleans """
        for rec in self:
            rec.partner_id = False
            rec.source_warehouse_id = False
            rec.destination_warehouse_id = False

    @api.depends('address_to', 'source_location_id', 'destination_location_id', 'd_city', 's_city')
    def _compute_name(self):
        """compute name"""
        for rec in self:
            name = ""
            if rec.address_to == "sc_address" and rec.s_city and rec.d_city:
                name = f"{rec.s_city} to {rec.d_city}"
            elif (rec.address_to == "location_address" and rec.source_location_id
                  and rec.destination_location_id):
                name = f"{rec.source_location_id.name} to {rec.destination_location_id.name}"
            rec.name = name

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

    @api.constrains('pickup_datetime', 'arrival_datetime')
    def _check_arrival_datetime(self):
        """check arrival date time"""
        for rec in self:
            if (rec.pickup_datetime and rec.arrival_datetime
                    and rec.arrival_datetime < rec.pickup_datetime):
                raise ValidationError(
                    _("In Routes page estimate arrival time cannot be earlier than estimate "
                      "pickup time."))

    def action_insert_line_service(self):
        """action insert line service"""
        if not self.total_charge > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': (_('Charges should be greater than zero!')),
                    'next': {'type': 'ir.actions.act_window_close'},
                    'sticky': False,
                }
            }
        self.env['freight.service'].create(
            {'service_id': self.env.ref('tk_freight.route_product_1').id,
             'name': "Route Charges : " + str(self.name),
             'qty': 1.0,
             'sale': self.total_charge,
             'cost': self.total_charge,
             'currency_id': self.env.company.currency_id.id,
             'shipment_id': self.shipment_id.id})
        self.line_added = True
        return True

    def action_create_delivery_order(self):
        """ Create Delivery Order """
        for rec in self:
            if not rec.shipment_id:
                continue

            shipment = rec.shipment_id
            delivery_product = shipment.delivery_product_id or self.env['product.product'].create({
                'name': shipment.name,
                'type': 'consu',
            })
            shipment.delivery_product_id = delivery_product.id

            picking_type_map = {
                'pickup': rec.source_warehouse_id.in_type_id,
                'delivery': rec.source_warehouse_id.out_type_id,
                'oncarriage': rec.source_warehouse_id.int_type_id
            }
            picking_type_id = picking_type_map.get(rec.type)

            if not picking_type_id:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': _('Picking Type not found from warehouse!'),
                    }
                }

            order_description = shipment.name
            if shipment.freight_packages:
                package_details = [f"Name : {pkg.package.name} - Qty : {pkg.qty}" for pkg in
                                   shipment.freight_packages if pkg.package and pkg.package.name]
                order_description += '\n---------------------------------\n' + '\n'.join(
                    package_details)

            if picking_type_id.default_location_src_id:
                location_id = picking_type_id.default_location_src_id.id
            elif rec.partner_id:
                location_id = rec.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if picking_type_id.default_location_dest_id:
                location_dest_id = picking_type_id.default_location_dest_id.id
            elif rec.partner_id:
                location_dest_id = rec.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            if rec.internal_transfer:
                location_dest_id = (
                    rec.destination_warehouse_id.lot_stock_id.id
                    if rec.destination_warehouse_id
                    else False
                )

            delivery_lines = {
                'product_id': delivery_product.id,
                'product_uom_qty': 1,
                'product_uom': delivery_product.uom_id.id,
                # 'name': order_description,
                'description_picking': order_description,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            }
            delivery_order_data = {
                'partner_id': rec.partner_id.id if rec.partner_id else False,
                'picking_type_id': picking_type_id.id,
                'origin': rec.shipment_id.name,
                'move_ids': [(0, 0, delivery_lines)],
                'freight_shipment_id': rec.shipment_id.id,
                'shipment_route_id': rec.id,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
            }
            delivery_order_id = self.env['stock.picking'].create(delivery_order_data)
            rec.delivery_order_id = delivery_order_id.id
        return True




class FreightVessel(models.Model):
    """Freight Vessel"""
    _name = 'freight.vessel'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(translate=True)
    global_zone = fields.Char(translate=True)
    country = fields.Many2one('res.country')
    active = fields.Boolean(default=True)
    imo_number = fields.Char(string="IMO", translate=True, size=7)
    flag_state = fields.Char(translate=True)
    port_of_registry = fields.Char(translate=True)
    capacity = fields.Char(string="Cargo Capacity", translate=True)
    engine = fields.Char(string="Type", translate=True)
    engine_power = fields.Char(string="Power", translate=True)
    speed = fields.Char(string="Speed(Knots)", translate=True)
    owner_id = fields.Many2one('res.partner', string='Shipping Line')

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if code.code and rec.code and rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another vessel."))


class FreightAirline(models.Model):
    """Freight Airline"""
    _name = 'freight.airline'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(translate=True)
    icao = fields.Char(string='ICAO', translate=True)
    country = fields.Many2one('res.country')
    active = fields.Boolean(default=True)
    aircraft_type = fields.Char(translate=True)
    capacity = fields.Char(string="Cargo Capacity", translate=True)
    owner_id = fields.Many2one('res.partner')

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if code.code and rec.code and rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another airline."))


class FreightIncoterms(models.Model):
    """Freight Incoterms"""
    _name = 'freight.incoterms'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(help="International Commercial Terms are a series of predefined commercial "
                            "terms used in international transactions.",
                       translate=True)
    active = fields.Boolean(default=True)

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if rec.code and code.code and rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another incoterms."))


class FreightPackage(models.Model):
    """Freight Package"""
    _name = 'freight.package'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(string='Name / Size', translate=True)
    container = fields.Boolean('Container/Box')
    item = fields.Boolean(string='Is Item')
    other = fields.Boolean()
    active = fields.Boolean(default=True)
    air = fields.Boolean()
    ocean = fields.Boolean()
    land = fields.Boolean()
    desc = fields.Char(string="Description", translate=True)
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    width = fields.Float(string='Width(cm)')
    volume = fields.Float('Volume (CBM)')
    gross_weight = fields.Float('Gross Weight (KG)')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    charge = fields.Monetary(string='Charges')

    @api.onchange('height', 'width', 'length')
    def onchange_package_cbm(self):
        """onchange package cbm"""
        for rec in self:
            rec.volume = (rec.height * rec.width * rec.length) / 1000000

    @api.constrains('air', 'ocean', 'land')
    def _check_air_ocean_land(self):
        """check air ocean land"""
        for rec in self:
            if not rec.air and not rec.ocean and not rec.land:
                raise ValidationError(_("Please select any one location air, ocean or land."))

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if code.code and rec.code and rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another package."))

    @api.constrains('container', 'item')
    def _check_container_item(self):
        """check container item"""
        for rec in self:
            if not rec.container and not rec.item:
                raise ValidationError(_("Please select anyone field container/box or is item."))


class FreightMoveType(models.Model):
    """Freight Move Type"""
    _name = 'freight.move.type'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(translate=True)
    active = fields.Boolean(default=True)

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if code.code and rec.code and rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another move type."))


class FreightDocuments(models.Model):
    """Document related to Freight Shipment"""
    _name = 'freight.documents'
    _description = __doc__
    _rec_name = 'type_id'

    freight_id = fields.Many2one('freight.shipment',
                                 string='Shipment',
                                 readonly=True)
    type_id = fields.Many2one('certificate.type', string='Type')
    document_date = fields.Date(string='Date', default=fields.Date.today())
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(translate=True)


class CertificateType(models.Model):
    """Type Of Certificate"""
    _name = 'certificate.type'
    _description = __doc__
    _rec_name = 'type'

    type = fields.Char(translate=True)


class PolicyRisk(models.Model):
    """Policy Risk Details"""
    _name = 'policy.risk'
    _description = __doc__

    name = fields.Char(string='Title', translate=True, required=True)
    desc = fields.Char(string='Description', translate=True)


class FrequentRoute(models.Model):
    """Frequent Route"""
    _name = 'freight.frequent.route'
    _description = __doc__

    name = fields.Char(translate=True)
    source_location_id = fields.Many2one('freight.port')
    destination_location_id = fields.Many2one('freight.port')

    @api.onchange('source_location_id', 'destination_location_id')
    def _onchange_source_destination(self):
        """onchange source destination"""
        for rec in self:
            if rec.source_location_id and rec.destination_location_id:
                rec.name = rec.source_location_id.name + \
                           " - " + rec.destination_location_id.name

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations(self):
        """check locations"""
        for rec in self:
            if (rec.source_location_id and rec.destination_location_id
                    and rec.source_location_id.id == rec.destination_location_id.id):
                raise ValidationError(
                    _("The source and destination locations cannot be the same \nplease change "
                      "one of the locations."))


class FreightMultipleInvoice(models.Model):
    """Multiple Invoice"""
    _name = "freight.multiple.invoice"
    _description = __doc__

    partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.move')
    date = fields.Date(default=fields.Date.today())
    amount = fields.Float()


class ShipmentLocation(models.Model):
    """Shipment Location"""
    _name = "shipment.location"
    _description = __doc__

    name = fields.Char(string="Title", translate=True)


class ShipmentActivity(models.Model):
    """Shipment Location Activity"""
    _name = "shipment.location.activity"
    _description = __doc__

    name = fields.Char(string="Activity", translate=True)


class TrackingTemplate(models.Model):
    """Tracking Template"""
    _name = 'tracking.template'
    _description = __doc__

    name = fields.Char(string="Title", translate=True)
    template_ids = fields.One2many(
        'tracking.template.line', 'template_id', string="Template")


class TrackingTemplateLine(models.Model):
    """Tracking Template Line"""
    _name = 'tracking.template.line'
    _description = __doc__
    _rec_name = "location_id"

    location_id = fields.Many2one('shipment.location', string="Location")
    activity_id = fields.Many2one('shipment.location.activity', string="Activity")
    template_id = fields.Many2one('tracking.template', string="Template")
