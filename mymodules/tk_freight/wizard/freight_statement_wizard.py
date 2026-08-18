# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class FreightStatementWizardLine(models.TransientModel):
    _name = 'freight.statement.wizard.line'
    _description = 'Statement Generation Wizard Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('freight.statement.wizard', ondelete='cascade')
    sequence = fields.Integer(default=10)
    select = fields.Boolean(default=False,
                           compute='_compute_select', store=False, readonly=False)
    service_id = fields.Many2one('freight.service', readonly=True)
    fee_state = fields.Selection(related='service_id.fee_state', readonly=True)
    selectable = fields.Boolean(compute='_compute_selectable')
    name = fields.Char(readonly=True)
    service_type = fields.Selection(related='service_id.service_type', readonly=True)
    partner_id = fields.Many2one('res.partner', compute='_compute_partner')
    qty = fields.Float(readonly=True)
    price_unit = fields.Monetary(currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    tax_code = fields.Char(readonly=True)
    tax_name = fields.Char(readonly=True)
    tax_rate = fields.Float(readonly=True)
    tax_amount = fields.Monetary(currency_field='currency_id', readonly=True)
    settlement_rate = fields.Float(digits=(12, 6), default=1.0, readonly=True)

    @api.depends('service_id')
    def _compute_partner(self):
        for line in self:
            s = line.service_id
            line.partner_id = s.shipper_id if s.service_type == 'shipper' else s.consignee_id

    @api.depends('service_id.fee_state', 'service_id.invoiced',
                 'service_id.statement_line_ids.statement_id.state',
                 'wizard_id.customer_id')
    def _compute_selectable(self):
        for line in self:
            s, w = line.service_id, line.wizard_id
            if not s or not w:
                line.selectable = False
                continue
            line.selectable = w._is_service_eligible(s, w.customer_id)

    @api.depends('service_id', 'wizard_id.selection_map_json')
    def _compute_select(self):
        for line in self:
            if not line.wizard_id or not line.service_id:
                line.select = False
                continue
            m = line.wizard_id._get_selection_map()
            line.select = m.get(str(line.service_id.id), False)


class FreightStatementWizard(models.TransientModel):
    _name = 'freight.statement.wizard'
    _description = 'Generate Settlement Statement'

    shipment_id = fields.Many2one('freight.shipment', required=True)
    customer_id = fields.Many2one('res.partner', domain="customer_domain")
    line_ids = fields.One2many('freight.statement.wizard.line', 'wizard_id')
    eligibility_summary = fields.Text(readonly=True)
    customer_domain = fields.Char(compute='_compute_customer_domain')
    selection_map_json = fields.Text(default='{}')

    # ===== Map 工具 =====
    def _get_selection_map(self):
        try:
            return json.loads(self.selection_map_json or '{}')
        except json.JSONDecodeError:
            return {}

    def get_selected_service_ids(self):
        m = self._get_selection_map()
        return [int(k) for k, v in m.items() if v]

    def _sync_select_from_line_command(self, line_id, select_val):
        line = self.env['freight.statement.wizard.line'].browse(line_id)
        if line.exists() and line.service_id:
            m = self._get_selection_map()
            sid = str(line.service_id.id)
            if select_val:
                m[sid] = True
            else:
                m.pop(sid, None)
            self.selection_map_json = json.dumps(m)
    # ====================

    @api.depends('shipment_id.shipper_id', 'shipment_id.consignee_id')
    def _compute_customer_domain(self):
        for rec in self:
            ids = [p.id for p in (rec.shipment_id.shipper_id, rec.shipment_id.consignee_id) if p]
            rec.customer_domain = repr([('id', 'in', ids)]) if ids else repr([('id', '=', False)])

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sid = res.get('shipment_id') or self.env.context.get('default_shipment_id')
        cid = res.get('customer_id') or self.env.context.get('default_customer_id')
        if sid and not cid:
            customers = self._customers_with_eligible_fees(self.env['freight.shipment'].browse(sid))
            if len(customers) == 1:
                res['customer_id'] = customers.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        关键修复：从前端传来的 virtual 行中按顺序提取 select 状态，
        在重建行之前写入 Map。
        """
        new_vals_list = []
        for vals in vals_list:
            # 提取前端 virtual 行的 select 顺序
            virtual_selects = []
            if 'line_ids' in vals:
                for cmd in vals['line_ids']:
                    if cmd[0] == 0 and isinstance(cmd[2], dict):
                        virtual_selects.append(bool(cmd[2].get('select', False)))

            # 先不传 line_ids 给 super()，避免创建无 service_id 的垃圾行
            clean_vals = {k: v for k, v in vals.items() if k != 'line_ids'}
            new_vals_list.append(clean_vals)

        records = super().create(new_vals_list)

        for rec in records:
            if rec.shipment_id:
                eligible = rec._eligible_services_for(rec.shipment_id, rec.customer_id)
                # 按 eligible 顺序初始化 Map（和 _rebuild_lines 里的顺序一致）
                if virtual_selects:
                    m = {}
                    for service, sel in zip(eligible.sorted('id'), virtual_selects):
                        if sel:
                            m[str(service.id)] = True
                    rec.selection_map_json = json.dumps(m)
                rec._rebuild_lines(eligible, rec.customer_id)

        return records

    def write(self, vals):
        """拦截用户在已有 wizard 上的 checkbox 变更。"""
        if 'line_ids' in vals:
            for cmd in vals['line_ids']:
                # (1, id, {select: ...}) — 更新已有行
                if cmd[0] == 1 and isinstance(cmd[2], dict) and cmd[2].get('select') is not None:
                    for rec in self:
                        rec._sync_select_from_line_command(cmd[1], bool(cmd[2]['select']))
        return super().write(vals)

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        self.customer_id = False
        self.selection_map_json = '{}'
        eligible = self._eligible_services_for(self.shipment_id, False)
        self._rebuild_lines(eligible, False)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if not self.shipment_id:
            self.line_ids = [(5, 0, 0)]
            self.eligibility_summary = False
            return
        eligible = self._eligible_services_for(self.shipment_id, self.customer_id)
        self._rebuild_lines(eligible, self.customer_id)

    def _rebuild_lines(self, eligible, customer):
        commands = [(5, 0, 0)]
        for service in eligible.sorted('id'):
            commands.append((0, 0, self._prepare_wizard_line(service)))
        self.line_ids = commands
        if customer:
            self.eligibility_summary = _('Eligible: %s / Listed: %s') % (len(eligible), len(eligible))
        else:
            self.eligibility_summary = _(
                'Showing confirmed fees of all shipment customers (%s). Select a customer to filter.'
            ) % len(eligible)

    # ===== 以下方法完全不变 =====
    def _is_service_eligible(self, service, customer=None, shipment=None):
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
        partner = service.shipper_id if service.service_type == 'shipper' else service.consignee_id
        if not partner:
            return False
        if customer:
            return partner.id == customer.id
        return partner.id in (shipment.shipper_id.id, shipment.consignee_id.id)

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
        return services.filtered(lambda s: self._is_service_eligible(s, customer, shipment))

    @api.model
    def _customers_with_eligible_fees(self, shipment):
        if not shipment:
            return self.env['res.partner']
        eligible = self._eligible_services_for(shipment, False)
        customers = self.env['res.partner']
        for s in eligible:
            p = s.shipper_id if s.service_type == 'shipper' else s.consignee_id
            if p:
                customers |= p
        return customers

    def _prepare_wizard_line(self, service):
        company = self.shipment_id.company_id or self.env.company
        currency = service.currency_id or company.currency_id
        product = service.service_id
        tax_rate = tax_code = tax_name = 0.0
        if product:
            t = product.taxes_id[:1]
            tax_rate = t.amount if t else 0.0
            tax_code = product.tax_code or False
            tax_name = product.tax_name or False
        rate = 1.0
        if currency != company.currency_id:
            rate = currency._convert(1.0, company.currency_id, company, fields.Date.context_today(self))
        return {
            'service_id': service.id, 'name': service.name, 'qty': service.qty,
            'price_unit': service.sale, 'currency_id': currency.id,
            'tax_code': tax_code, 'tax_name': tax_name, 'tax_rate': tax_rate,
            'tax_amount': service.sale * service.qty * tax_rate / 100.0,
            'settlement_rate': rate,
        }

    def action_generate_statement(self):
        self.ensure_one()
        selected_ids = self.get_selected_service_ids()
        if not selected_ids:
            raise ValidationError(_('Please select at least one fee.'))
        selected_services = self.env['freight.service'].browse(selected_ids)

        if self.customer_id and self.customer_id.id not in (
                self.shipment_id.shipper_id.id, self.shipment_id.consignee_id.id):
            raise ValidationError(_('The selected customer is not the shipper/consignee.'))
        not_ok = selected_services.filtered(lambda s: not self._is_service_eligible(s, self.customer_id))
        if not_ok:
            raise ValidationError(_('Fee(s) "%s" are no longer selectable.') % ','.join(not_ok.mapped('name')))

        customer = self.customer_id
        if not customer:
            customers = self.env['res.partner']
            for s in selected_services:
                p = s.shipper_id if s.service_type == 'shipper' else s.consignee_id
                if p: customers |= p
            if len(customers) != 1:
                raise ValidationError(_('Please select fees of the same customer.'))
            customer = customers

        ordered = selected_services.sorted('id')
        self.env.cr.execute('SELECT id FROM freight_service WHERE id = ANY(%s) ORDER BY id FOR UPDATE', [ordered.ids])
        ordered.invalidate_recordset()
        for s in ordered:
            if not self._is_service_eligible(s, customer):
                raise ValidationError(_('Fee "%s" changed state.') % s.name)

        statement = self.env['freight.statement'].create({
            'freight_operation_id': self.shipment_id.id, 'customer_id': customer.id,
            'settlement_date': fields.Date.context_today(self),
        })

        
        line_vals = []
        for index, service in enumerate(ordered, start=1):
            vals = self._prepare_wizard_line(service)
            vals.pop('service_id', None)          # ← 加回这行！
            vals.update({
                'statement_id': statement.id,
                'freight_service_id': service.id,
                'sequence': 10 * index,
            })
            line_vals.append(vals)
        self.env['freight.statement.line'].create(line_vals)
        

        statement.statement_line_ids.mapped('freight_service_id').write({'fee_state': 'used'})
        return {'type': 'ir.actions.act_window', 'name': _('Settlement Statement'),
                'res_model': 'freight.statement', 'res_id': statement.id, 'view_mode': 'form', 'target': 'current'}
