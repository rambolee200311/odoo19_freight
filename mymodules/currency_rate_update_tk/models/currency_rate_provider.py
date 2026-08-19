from odoo import models, fields


class CurrencyRateProvider(models.Model):
    _inherit = 'currency.rate.provider'

    # 是否在自动更新范围内（OCA 原版默认所有启用 provider 都更新）
    active_for_auto = fields.Boolean(
        string='纳入自动更新',
        default=True,
        help='取消勾选后，Cron 自动更新将跳过此币别',
    )

    # 审计字段（只读展示）
    last_rate = fields.Float(
        string='上次汇率',
        readonly=True,
        digits=(12, 6),
    )
    last_update = fields.Datetime(
        string='上次更新时间',
        readonly=True,
    )
    update_status = fields.Selection([
        ('success', '成功'),
        ('error', '失败'),
        ('never', '未更新'),
    ], string='状态', default='never', readonly=True)

    # 波动阈值（每币别可单独设置，覆盖全局默认）
    volatility_threshold = fields.Float(
        string='波动告警阈值 (%)',
        default=20.0,
        help='超过此阈值将阻止自动写入，需人工确认',
    )
