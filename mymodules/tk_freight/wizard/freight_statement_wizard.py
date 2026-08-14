# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FreightStatementWizard(models.TransientModel):
    """Generate a settlement statement from selected freight.service records."""
    _name = 'freight.statement.wizard'
    _description = 'Generate Settlement Statement'

    shipment_id = fields.Many2one('freight.shipment', string='Freight Operation',
                                  required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        domain="customer_domain")
    selected_service_ids = fields.Many2many(
        'freight.service',
        'freight_statement_wizard_service_rel',
        'wizard_id',
        'service_id',
        string='Selected Fees')
    customer_domain = fields.Char(string='Customer Domain',
                                  compute='_compute_customer_domain')
    eligible_service_domain = fields.Char(string='Eligible Fee Domain',
                                          compute='_compute_eligible_service_domain')

    @api.depends('shipment_id.shipper_id', 'shipment_id.consignee_id')
    def _compute_customer_domain(self):
        for rec in self:
            ids = []
            for partner in (rec.shipment_id.shipper_id, rec.shipment_id.consignee_id):
                if partner:
                    ids.append(partner.id)
            rec.customer_domain = repr([('id', 'in', ids)]) if ids \
                else repr([('id', '=', False)])

    @api.depends('shipment_id', 'customer_id')
    def _compute_eligible_service_domain(self):
        for rec in self:
            ids = rec._eligible_services_for(
                rec.shipment_id, rec.customer_id).ids
            rec.eligible_service_domain = repr([('id', 'in', ids)]) if ids \
                else repr([('id', '=', False)])

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
            eligible = rec._eligible_services_for(
                rec.shipment_id, rec.customer_id)
            rec.selected_service_ids = eligible
        return records

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        self.customer_id = False
        eligible = self._eligible_services_for(self.shipment_id, False)
        self.selected_service_ids = eligible

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        eligible = self._eligible_services_for(
            self.shipment_id, self.customer_id)
        self.selected_service_ids = eligible

    def _is_service_eligible(self, service, customer=None, shipment=None):
        """Single eligibility authority for the wizard selection domain."""
        if not service:
            return False
        shipment = shipment or self.shipment_id or service.shipment_id
        if not shipment or service.shipment_id.id != shipment.id:
            return False
        if service.service_type not in ('shipper', 'consignee'):
            return False
        if service.fee_state != 'confirmed' or service.invoiced:
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

    def _prepare_statement_line_vals(self, service, statement, index):
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
            'statement_id': statement.id,
            'freight_service_id': service.id,
            'sequence': 10 * index,
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
        if self.customer_id:
            customer = self.customer_id
        else:
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
        if customer.id not in (
                self.shipment_id.shipper_id.id, self.shipment_id.consignee_id.id):
            raise ValidationError(_(
                'The selected customer is not the shipper/consignee of this '
                'freight operation.'))
        for service in services:
            if not self._is_service_eligible(service, customer):
                raise ValidationError(_(
                    'Fee "%s" is no longer eligible for this statement. Refresh '
                    'the wizard and select the fees again.') % service.name)
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
            line_vals.append(
                self._prepare_statement_line_vals(service, statement, index))
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
