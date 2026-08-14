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
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='currency_id',
                                 readonly=True)
    settlement_rate = fields.Float(string='Settlement Rate', digits=(12, 6),
                                   default=1.0, readonly=True)

    @api.depends('service_id')
    def _compute_partner(self):
        for line in self:
            service = line.service_id
            line.partner_id = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id

    @api.depends('service_id.fee_state', 'service_id.invoiced',
                 'service_id.statement_line_ids.statement_id.state',
                 'wizard_id.customer_id')
    def _compute_selectable(self):
        for line in self:
            service = line.service_id
            wizard = line.wizard_id
            if not service or not wizard:
                line.selectable = False
                continue
            line.selectable = wizard._is_service_eligible(
                service, wizard.customer_id)


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
    eligibility_summary = fields.Text(string='Eligibility Summary', readonly=True)
    customer_domain = fields.Char(string='Customer Domain',
                                  compute='_compute_customer_domain')

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
                # Client-submitted line commands may arrive without the fee link;
                # always rebuild the rows server-side so the checkbox list is
                # backed by real freight.service records.
                rec.with_context(wizard_rebuild=True)._rebuild_lines(
                    eligible, rec.customer_id)
        return records

    def write(self, vals):
        # Lifecycle contract: ordinary writes preserve user select and never
        # rebuild the line collection. Only structural line commands (create /
        # delete / clear) restore the authoritative eligible set.
        if self.env.context.get('wizard_rebuild'):
            return super().write(vals)
        if 'line_ids' in vals:
            codes = {cmd[0] for cmd in vals['line_ids']}
            if codes & {2, 3, 5, 6}:
                # User cannot delete/clear rows; restore the authoritative set.
                res = super().write(vals)
                for rec in self:
                    if rec.shipment_id:
                        eligible = rec._eligible_services_for(
                            rec.shipment_id, rec.customer_id)
                        rec.with_context(wizard_rebuild=True)._rebuild_lines(
                            eligible, rec.customer_id)
                return res
            if codes & {0}:
                # Web client rebuilds rows as create commands. Preserve the
                # client-submitted select state keyed by service_id, then align
                # the rows to the authoritative eligible set.
                res = super().write(vals)
                for rec in self:
                    if rec.shipment_id:
                        eligible = rec._eligible_services_for(
                            rec.shipment_id, rec.customer_id)
                        select_map = {
                            line.service_id.id: line.select
                            for line in rec.line_ids if line.service_id
                        }
                        rec.with_context(wizard_rebuild=True)._rebuild_lines(
                            eligible, rec.customer_id, select_map=select_map)
                return res
        return super().write(vals)

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        self.customer_id = False
        eligible = self._eligible_services_for(self.shipment_id, False)
        self._rebuild_lines(eligible, False)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.shipment_id:
            self.line_ids = [(5, 0, 0)]
            self.eligibility_summary = False
            return
        eligible = self._eligible_services_for(
            self.shipment_id, self.customer_id)
        self._rebuild_lines(eligible, self.customer_id)

    def _rebuild_lines(self, eligible, customer, select_map=None):
        commands = [(5, 0, 0)]
        for service in eligible.sorted('id'):
            vals = self._prepare_wizard_line(service)
            if select_map is None:
                vals['select'] = True
            else:
                vals['select'] = select_map.get(service.id, False)
            commands.append((0, 0, vals))
        self.line_ids = commands
        if customer:
            self.eligibility_summary = _(
                'Eligible: %s / Listed: %s') % (len(eligible), len(eligible))
        else:
            self.eligibility_summary = _(
                'Showing confirmed fees of all shipment customers (%s). '
                'Select a customer to filter.') % len(eligible)

    def _is_service_eligible(self, service, customer=None, shipment=None):
        """Single eligibility authority shared by list, selectable and generate."""
        if not service:
            return False
        shipment = shipment or self.shipment_id or service.shipment_id
        if not shipment or service.shipment_id.id != shipment.id:
            return False
        if service.service_type not in ('shipper', 'consignee'):
            return False
        if service.fee_state != 'confirmed' or service.invoiced:
            return False
        if any(ref.statement_id.state in ('draft', 'confirmed', 'draft_invoice')
               for ref in service.statement_line_ids):
            return False
        partner = service.shipper_id if service.service_type == 'shipper' \
            else service.consignee_id
        if not partner:
            return False
        if customer:
            return partner.id == customer.id
        return partner.id in (
            shipment.shipper_id.id, shipment.consignee_id.id)

    @api.model
    def _eligible_services_for(self, shipment, customer):
        if not shipment:
            return self.env['freight.service']
        services = self.env['freight.service'].search([
            ('shipment_id', '=', shipment.id),
            ('service_type', 'in', ('shipper', 'consignee')),
            ('fee_state', '=', 'confirmed'),
            ('invoiced', '=', False),
        ])
        return services.filtered(
            lambda service: self._is_service_eligible(service, customer, shipment))

    def _get_eligible_services(self):
        self.ensure_one()
        return self._eligible_services_for(self.shipment_id, self.customer_id)

    @api.model
    def _customers_with_eligible_fees(self, shipment):
        if not shipment:
            return self.env['res.partner']
        eligible = self._eligible_services_for(shipment, False)
        customers = self.env['res.partner']
        for service in eligible:
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
        selected = self.line_ids.filtered('select')
        if not selected:
            raise ValidationError(_('Please select at least one fee.'))
        missing_link = selected.filtered(lambda line: not line.service_id)
        if missing_link:
            raise ValidationError(_(
                'Selected fee rows have no freight service. Reopen the statement '
                'wizard and select the fees again.'))
        if self.customer_id and self.customer_id.id not in (
                self.shipment_id.shipper_id.id, self.shipment_id.consignee_id.id):
            raise ValidationError(_(
                'The selected customer is not the shipper/consignee of this '
                'freight operation.'))
        not_selectable = selected.filtered(lambda line: not line.selectable)
        if not_selectable:
            raise ValidationError(_(
                'Fee(s) "%s" are no longer selectable. Refresh the wizard and '
                'select the fees again.') % ', '.join(
                    not_selectable.mapped('name')))
        services = selected.mapped('service_id')
        missing_targets = []
        for service in services:
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
        # Serialize concurrent generation and re-validate the authoritative fee
        # rows after the lock (B-64): the pre-lock checks are only user feedback.
        ordered_services = services.sorted('id')
        self.env.cr.execute(
            'SELECT id FROM freight_service WHERE id = ANY(%s) '
            'ORDER BY id FOR UPDATE',
            [ordered_services.ids],
        )
        ordered_services.invalidate_recordset()
        for service in ordered_services:
            if not self._is_service_eligible(service, customer):
                raise ValidationError(_(
                    'Fee "%s" is no longer eligible for this statement. Refresh '
                    'the wizard and select the fees again.') % service.name)
        statement = self.env['freight.statement'].create({
            'freight_operation_id': self.shipment_id.id,
            'customer_id': customer.id,
            'settlement_date': fields.Date.context_today(self),
        })
        line_vals = []
        for index, service in enumerate(ordered_services, start=1):
            vals = self._prepare_wizard_line(service)
            vals.pop('service_id', None)
            vals.update({
                'statement_id': statement.id,
                'freight_service_id': service.id,
                'sequence': 10 * index,
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
