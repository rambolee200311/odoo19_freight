# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FreightStatementWizardLine(models.TransientModel):
    """Selectable freight.service row inside the statement generation wizard."""
    _name = 'freight.statement.wizard.line'
    _description = 'Statement Generation Wizard Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('freight.statement.wizard', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    select = fields.Boolean(string='Select', default=False)
    service_id = fields.Many2one('freight.service', string='Freight Service',
                                 readonly=True)
    fee_state = fields.Selection(related='service_id.fee_state',
                                 string='Fee State', readonly=True)
    selectable = fields.Boolean(string='Selectable', compute='_compute_selectable')
    name = fields.Char(string='Description', readonly=True)
    service_type = fields.Selection(related='service_id.service_type',
                                    string='Service To', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Invoice To',
                                 compute='_compute_partner')
    qty = fields.Float(string='Quantity', readonly=True)
    price_unit = fields.Monetary(string='Unit Price', currency_field='currency_id',
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    tax_code = fields.Char(string='Tax Code', readonly=True)
    tax_name = fields.Char(string='Tax Name', readonly=True)
    tax_rate = fields.Float(string='Tax Rate (%)', readonly=True)
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id')
    settlement_rate = fields.Float(string='Settlement Rate', digits=(12, 6), default=1.0)

    @api.depends('service_id')
    def _compute_partner(self):
        for line in self:
            service = line.service_id
            line.partner_id = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id

    @api.depends('service_id.fee_state', 'service_id.invoiced',
                 'service_id.statement_line_ids.statement_id.state')
    def _compute_selectable(self):
        for line in self:
            service = line.service_id
            line.selectable = (
                service.fee_state == 'confirmed'
                and not service.invoiced
                and not any(
                    ref.statement_id.state in ('draft', 'confirmed', 'draft_invoice')
                    for ref in service.statement_line_ids))

    def toggle_select(self):
        for line in self:
            line.select = not line.select
        for wizard in self.mapped('wizard_id'):
            wizard.selected_service_ids = [(6, 0, wizard.line_ids.filtered(
                'select').mapped('service_id').ids)]
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class FreightStatementWizard(models.TransientModel):
    """Generate a settlement statement from selected freight.service lines."""
    _name = 'freight.statement.wizard'
    _description = 'Generate Settlement Statement'

    shipment_id = fields.Many2one('freight.shipment', string='Freight Operation',
                                  required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        domain="['|',('shipper','=',True),('consignee','=',True)]")
    line_ids = fields.One2many('freight.statement.wizard.line', 'wizard_id',
                               string='Eligible Fees')
    selected_service_ids = fields.Many2many(
        'freight.service', string='Selected Fees')
    eligible_service_ids = fields.Many2many(
        'freight.service', string='Eligible Fee Ids',
        compute='_compute_eligible_service_ids')
    eligibility_summary = fields.Text(string='Eligibility Summary', readonly=True)
    customer_domain = fields.Char(string='Customer Domain',
                                  compute='_compute_customer_domain')

    @api.depends('shipment_id', 'customer_id')
    def _compute_eligible_service_ids(self):
        for rec in self:
            rec.eligible_service_ids = rec._eligible_services_for(
                rec.shipment_id, rec.customer_id)

    @api.depends('shipment_id.shipper_id', 'shipment_id.consignee_id')
    def _compute_customer_domain(self):
        for rec in self:
            ids = []
            for partner in (rec.shipment_id.shipper_id, rec.shipment_id.consignee_id):
                if partner:
                    ids.append(partner.id)
            if ids:
                rec.customer_domain = repr([('id', 'in', ids)])
            else:
                rec.customer_domain = repr([('id', '=', False)])

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        shipment_id = res.get('shipment_id') or self.env.context.get(
            'default_shipment_id')
        customer_id = res.get('customer_id') or self.env.context.get(
            'default_customer_id')
        if shipment_id and not customer_id:
            shipment = self.env['freight.shipment'].browse(shipment_id)
            customers = self._customers_with_eligible_fees(shipment)
            if len(customers) == 1:
                res['customer_id'] = customers.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.shipment_id:
                eligible = rec._eligible_services_for(
                    rec.shipment_id, rec.customer_id)
                rec._populate_lines(eligible, rec.customer_id)
                rec.selected_service_ids = [(6, 0, eligible.ids)]
        return records

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        self.customer_id = False
        eligible = self._eligible_services_for(self.shipment_id, False)
        self._populate_lines(eligible, False)
        self.selected_service_ids = [(6, 0, eligible.ids)]

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.shipment_id:
            self.line_ids = [(5, 0, 0)]
            self.selected_service_ids = [(5, 0, 0)]
            self.eligibility_summary = False
            return
        eligible = self._eligible_services_for(
            self.shipment_id, self.customer_id)
        self._populate_lines(eligible, self.customer_id)
        self.selected_service_ids = [(6, 0, eligible.ids)]

    def _populate_lines(self, eligible, customer):
        commands = [(5, 0, 0)]
        for service in eligible.sorted('id'):
            vals = self._prepare_wizard_line(service)
            vals['select'] = True
            commands.append((0, 0, vals))
        self.line_ids = commands
        if customer:
            self.eligibility_summary = _(
                'Eligible: %s / Listed: %s') % (len(eligible), len(eligible))
        else:
            self.eligibility_summary = _(
                'Showing confirmed fees of all shipment customers (%s). '
                'Select a customer to filter.') % len(eligible)

    @api.model
    def _eligible_services_for(self, shipment, customer):
        if not shipment:
            return self.env['freight.service']
        active_statements = self.env['freight.statement'].search([
            ('freight_operation_id', '=', shipment.id),
            ('state', 'in', ('draft', 'confirmed', 'draft_invoice')),
        ])
        used_service_ids = active_statements.statement_line_ids.mapped(
            'freight_service_id').ids
        services = self.env['freight.service'].search([
            ('shipment_id', '=', shipment.id),
            ('service_type', 'in', ('shipper', 'consignee')),
            ('fee_state', '=', 'confirmed'),
            ('invoiced', '=', False),
        ])
        eligible = self.env['freight.service']
        for service in services:
            if service.id in used_service_ids:
                continue
            partner = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id
            if not partner:
                continue
            if customer and partner.id != customer.id:
                continue
            if not customer and partner.id not in (
                    shipment.shipper_id.id, shipment.consignee_id.id):
                continue
            eligible |= service
        return eligible

    def _get_eligible_services(self):
        self.ensure_one()
        return self._eligible_services_for(self.shipment_id, self.customer_id)

    @api.model
    def _customers_with_eligible_fees(self, shipment):
        if not shipment:
            return self.env['res.partner']
        services = self.env['freight.service'].search([
            ('shipment_id', '=', shipment.id),
            ('service_type', 'in', ('shipper', 'consignee')),
            ('fee_state', '=', 'confirmed'),
            ('invoiced', '=', False),
        ])
        active_statements = self.env['freight.statement'].search([
            ('freight_operation_id', '=', shipment.id),
            ('state', 'in', ('draft', 'confirmed', 'draft_invoice')),
        ])
        used_ids = active_statements.statement_line_ids.mapped(
            'freight_service_id').ids
        customers = self.env['res.partner']
        for service in services:
            if service.id in used_ids:
                continue
            partner = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id
            if partner:
                customers |= partner
        return customers

    def _prepare_wizard_line(self, service):
        company = self.shipment_id.company_id or self.env.company
        currency = service.currency_id or company.currency_id
        product = service.service_id
        tax_rate = 0.0
        tax_code = False
        tax_name = False
        if product:
            sale_tax = product.taxes_id[:1]
            tax_rate = sale_tax.amount if sale_tax else 0.0
            tax_code = product.tax_code or False
            tax_name = product.tax_name or False
        settlement_rate = 1.0
        if currency != company.currency_id:
            settlement_rate = currency._convert(
                1.0, company.currency_id, company, fields.Date.context_today(self))
        return {
            'service_id': service.id,
            'name': service.name,
            'qty': service.qty,
            'price_unit': service.sale,
            'currency_id': currency.id,
            'tax_code': tax_code,
            'tax_name': tax_name,
            'tax_rate': tax_rate,
            'tax_amount': service.sale * service.qty * tax_rate / 100.0,
            'settlement_rate': settlement_rate,
        }

    def action_generate_statement(self):
        self.ensure_one()
        services = self.selected_service_ids
        if not services:
            raise ValidationError(_('Please select at least one fee.'))
        eligible = self._eligible_services_for(
            self.shipment_id, self.customer_id)
        not_eligible = services - eligible
        if not_eligible:
            raise ValidationError(_(
                'Fee(s) "%s" are no longer eligible for this statement. Refresh '
                'the wizard and select the fees again.') % ', '.join(
                    not_eligible.mapped('name')))
        missing_targets = []
        for service in services:
            if service.service_type == 'vendor':
                raise ValidationError(_(
                    'Vendor cost lines cannot be included in a customer statement.'))
            partner = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id
            if not partner:
                missing_targets.append(service.name)
        if self.customer_id:
            customer = self.customer_id
        else:
            if missing_targets:
                raise ValidationError(_(
                    'Selected fees have no invoice target: %s. Add the shipper/consignee '
                    'before generating a statement.') % ', '.join(missing_targets))
            customers = self.env['res.partner']
            for service in services:
                partner = service.shipper_id if service.service_type == 'shipper' \
                    else service.consignee_id
                if partner:
                    customers |= partner
            if not customers:
                raise ValidationError(_(
                    'Selected fees have no invoice target. Add the shipper/consignee '
                    'before generating a statement.'))
            if len(customers) > 1:
                raise ValidationError(_(
                    'Please select fees of the same customer, or choose a customer '
                    'before generating a statement.'))
            customer = customers
        # Serialize concurrent generation: one fee can only be occupied by one
        # non-voided statement (fee_statement_invariant).
        self.env.cr.execute(
            'SELECT id FROM freight_service WHERE id = ANY(%s) FOR UPDATE',
            [services.ids],
        )
        services.invalidate_recordset()
        for service in services:
            if service.fee_state != 'confirmed':
                raise ValidationError(_(
                    'Fee "%s" is no longer in confirmed state. Refresh the wizard '
                    'and check the fee state.' % service.name))
        statement = self.env['freight.statement'].create({
            'freight_operation_id': self.shipment_id.id,
            'customer_id': customer.id,
            'settlement_date': fields.Date.context_today(self),
        })
        line_vals = []
        for service in services.sorted('id'):
            vals = self._prepare_wizard_line(service)
            vals.pop('service_id', None)
            vals.update({
                'statement_id': statement.id,
                'freight_service_id': service.id,
                'sequence': 10,
            })
            line_vals.append(vals)
        self.env['freight.statement.line'].create(line_vals)
        statement_fees = statement.statement_line_ids.mapped('freight_service_id')
        if any(fee.fee_state != 'confirmed' for fee in statement_fees):
            raise ValidationError(_(
                'One or more fees changed state during statement creation. '
                'The transaction was rolled back.'))
        statement_fees.write({'fee_state': 'used'})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Settlement Statement'),
            'res_model': 'freight.statement',
            'res_id': statement.id,
            'view_mode': 'form',
            'target': 'current',
        }
