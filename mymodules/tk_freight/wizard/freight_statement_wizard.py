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
    select = fields.Boolean(string='Select', default=True)
    service_id = fields.Many2one('freight.service', string='Freight Service',
                                 readonly=True)
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


class FreightStatementWizard(models.TransientModel):
    """Generate a settlement statement from selected freight.service lines."""
    _name = 'freight.statement.wizard'
    _description = 'Generate Settlement Statement'

    shipment_id = fields.Many2one('freight.shipment', string='Freight Operation',
                                  required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="['|',('shipper','=',True),('consignee','=',True)]")
    line_ids = fields.One2many('freight.statement.wizard.line', 'wizard_id',
                               string='Selectable Services')

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        self.customer_id = False
        self.line_ids = [(5, 0, 0)]

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        commands = [(5, 0, 0)]
        for service in self._get_eligible_services():
            commands.append((0, 0, self._prepare_wizard_line(service)))
        self.line_ids = commands

    def _get_eligible_services(self):
        self.ensure_one()
        if not self.shipment_id or not self.customer_id:
            return self.env['freight.service']
        active_statements = self.env['freight.statement'].search([
            ('freight_operation_id', '=', self.shipment_id.id),
            ('customer_id', '=', self.customer_id.id),
            ('state', 'in', ('draft', 'confirmed', 'draft_invoice')),
        ])
        used_service_ids = active_statements.statement_line_ids.mapped(
            'freight_service_id').ids
        services = self.env['freight.service'].search([
            ('shipment_id', '=', self.shipment_id.id),
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
            if not partner or partner.id != self.customer_id.id:
                continue
            eligible |= service
        return eligible

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
            raise ValidationError(_('Please select at least one service line.'))
        for line in selected:
            service = line.service_id
            if service.service_type == 'vendor':
                raise ValidationError(_(
                    'Vendor cost lines cannot be included in a customer statement.'))
            partner = service.shipper_id if service.service_type == 'shipper' \
                else service.consignee_id
            if not partner:
                raise ValidationError(_(
                    'Service "%s" has no invoice target. Add the shipper/consignee '
                    'before generating a statement.' % service.name))
            if service.fee_state != 'confirmed':
                raise ValidationError(_(
                    'Fee "%s" is no longer in confirmed state. Refresh the wizard '
                    'and check the fee state.' % service.name))
        statement = self.env['freight.statement'].create({
            'freight_operation_id': self.shipment_id.id,
            'customer_id': self.customer_id.id,
            'settlement_date': fields.Date.context_today(self),
        })
        line_vals = []
        for line in selected.sorted('sequence'):
            line_vals.append({
                'statement_id': statement.id,
                'freight_service_id': line.service_id.id,
                'sequence': line.sequence or 10,
                'name': line.name,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'currency_id': line.currency_id.id,
                'tax_code': line.tax_code or False,
                'tax_name': line.tax_name or False,
                'tax_rate': line.tax_rate or 0.0,
                'tax_amount': line.tax_amount or 0.0,
                'settlement_rate': line.settlement_rate or 1.0,
            })
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
