from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UpdateRatesWizard(models.TransientModel):
    _name = 'update.rates.wizard'
    _description = '手动更新汇率向导'

    provider_id = fields.Many2one(
        'res.currency.rate.provider',
        string='汇率服务',
    )
    test_mode = fields.Boolean(
        string='仅测试连接（不写入）',
        default=False,
    )
    result = fields.Text(
        string='结果',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # 默认取第一个启用的 ECB provider
        provider = self.env['res.currency.rate.provider'].search([
            ('service', '=', 'ECB'),
            ('active', '=', True),
        ], limit=1)
        if provider:
            res['provider_id'] = provider.id
        return res

    def action_update(self):
        self.ensure_one()
        provider = self.provider_id
        if not provider:
            raise UserError(_('请先选择汇率服务'))

        if self.test_mode:
            try:
                # 修问题1：_get_supported_currencies返回的是list，不是dict
                rates = provider._get_supported_currencies()
                self.result = _('连接成功！可用货币：%s') % ', '.join(rates)
            except Exception as e:
                self.result = _('连接失败：%s') % str(e)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'update.rates.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        # 修问题2：补OCA要求的日期参数，用当天日期
        today = fields.Date.context_today(self)
        # provider._update(today, today, newest_only=True)
        provider.with_context(trigger_type='manual')._update(today, today, newest_only=True)
        self.result = _('更新完成，请查看审计日志')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.rates.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }