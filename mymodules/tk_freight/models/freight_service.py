import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

# Fields the invoicing/billing/statement workflow must still be able to set
# after a fee is confirmed/used/canceled; only the fields NOT in this set
# are treated as immutable "business data" of the fee.
FEE_EDITABLE_IN_LOCKED_STATE = {
    'fee_state', 'status', 'invoiced', 'customer_invoice',
    'vendor_invoiced', 'vendor_invoice', 'statement_line_ids',
}
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
    fee_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('used', 'Used'),
        ('canceled', 'Canceled'),
    ], string='Fee State', default='draft', required=True, tracking=True)
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
    # DEPRECATED (Sprint4-4-2): fee_state is the single authority for fee
    # usability/locking; statement_locked is kept for legacy compatibility only
    # and must not be used by new business logic.
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

    # 2026-08-18 lijianqiang
    # 货运单新增费用并 confirm 后，保存货运单报错 → Fees in confirmed/used/canceled state cannot be modified.
    # 这是一个阻塞正常操作的 bug——用户无法在同一个货运单保存动作中完成"新增费用 → confirm → 保存"，必须拆成两步（先保存草稿 → 再 confirm），体验不合理且容易误操作。
    def write(self, vals):
        for rec in self:
            if rec.fee_state not in ('confirmed', 'used', 'canceled'):
                continue

            changed = False
            changed_field = None
            old_value = None
            new_value = None

            for field_name, new_val in vals.items():
                if field_name in FEE_EDITABLE_IN_LOCKED_STATE:
                    continue

                field = rec._fields[field_name]
                current = rec[field_name]

                if field.type in ('one2many', 'many2many'):
                    changed = True
                    changed_field = field_name
                    break

                if field.type == 'many2one':
                    current = current.id if current else False
                    # first-time linkage (e.g. ORM attaching a new fee to its
                    # shipment) is not a business-data change, only reassignment is
                    if not current and new_val:
                        continue

                if field.type == 'float':
                    digits = field.get_digits(rec.env)
                    precision = digits[1] if digits else 4
                    if float_compare(current or 0.0, new_val or 0.0,
                                      precision_digits=precision) != 0:
                        changed = True
                        changed_field = field_name
                        old_value = current
                        new_value = new_val
                        break
                    continue

                if current != new_val:
                    changed = True
                    changed_field = field_name
                    old_value = current
                    new_value = new_val
                    break

            if changed:
                _logger.error(
                    "FEE WRITE BLOCKED: service_id=%s, fee_state=%s, "
                    "changed_field=%s, old_value=%s, new_value=%s, full_vals=%s",
                    rec.id, rec.fee_state, changed_field, old_value, new_value, vals
                )
                raise ValidationError(_(
                    'Fees in confirmed/used/canceled state cannot be modified. '
                    '(Field "%s" changed from "%s" to "%s")'
                ) % (changed_field, old_value, new_value))

        return super().write(vals)

    def write_old1(self, vals):
        for rec in self:
            if rec.fee_state in ('confirmed', 'used', 'canceled') and \
                    set(vals) - {'fee_state'}:
                raise ValidationError(_(
                    'Fees in confirmed/used/canceled state cannot be modified.'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.fee_state in ('confirmed', 'used', 'canceled'):
                raise ValidationError(_(
                    'Fees in confirmed/used/canceled state cannot be deleted.'))
            if rec.statement_line_ids:
                raise ValidationError(_(
                    'Draft fees referenced by statements cannot be deleted. '
                    'Cancel the fee instead if it is no longer needed.'))
        return super().unlink()

    def action_confirm_fee(self):
        for rec in self:
            if rec.fee_state != 'draft':
                raise ValidationError(_('Only draft fees can be confirmed.'))
        self.write({'fee_state': 'confirmed'})
        return True

    def action_unconfirm_fee(self):
        for rec in self:
            if rec.fee_state != 'confirmed':
                raise ValidationError(_('Only confirmed fees can be unconfirmed.'))
            if any(line.statement_id.state in ('draft', 'confirmed', 'draft_invoice')
                   for line in rec.statement_line_ids):
                raise ValidationError(_(
                    'Cannot unconfirm a fee that is referenced by an active statement.'))
        self.write({'fee_state': 'draft'})
        return True

    def action_cancel_fee(self):
        for rec in self:
            if rec.fee_state != 'draft':
                raise ValidationError(_('Only draft fees can be canceled.'))
        self.write({'fee_state': 'canceled'})
        return True

    def action_copy_as_draft(self):
        copies = self.env['freight.service']
        for rec in self:
            if rec.fee_state != 'canceled':
                raise ValidationError(_('Only canceled fees can be copied as draft.'))
            copies |= rec.copy(default={
                'fee_state': 'draft',
                'status': 'pending',
                'invoiced': False,
                'vendor_invoiced': False,
            })
        return copies

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