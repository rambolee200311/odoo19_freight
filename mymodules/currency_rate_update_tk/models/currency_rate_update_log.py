from odoo import models, fields, api
import traceback


class CurrencyRateUpdateLog(models.Model):
    _name = 'currency.rate.update.log'
    _description = '汇率更新审计日志（全量故障排查信息）'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # ===== 基础身份（定位是谁的操作）=====
    provider_id = fields.Many2one(
        'res.currency.rate.provider',
        string='汇率服务商',
        index=True,
        ondelete='set null'
    )
    company_id = fields.Many2one(
        'res.company',
        string='所属公司',
        default=lambda self: self.env.company,
        index=True
    )
    trigger_type = fields.Selection([
        ('manual', '手动更新'),
        ('cron', '定时任务'),
        ('api', '接口调用'),
        ('test', '连接测试')
    ], string='触发方式', required=True, index=True)
    create_uid = fields.Many2one('res.users', string='操作人', readonly=True)

    # ===== 执行过程（定位执行状态）=====
    state = fields.Selection([
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('partial', '部分成功')
    ], string='执行状态', required=True, index=True, default='running')
    start_time = fields.Datetime(string='开始时间', required=True)
    end_time = fields.Datetime(string='结束时间')
    duration_ms = fields.Integer(
        string='耗时(毫秒)',
        compute='_compute_duration',
        store=True
    )

    # ===== 业务结果（定位业务正确性）=====
    rates_count = fields.Integer(string='更新笔数', default=0)
    updated_currencies = fields.Char(
        string='更新币种',
        help='本次更新的币种代码，如USD,CNY,JPY'
    )
    rate_ids = fields.Many2many(
        'res.currency.rate',
        string='关联的汇率记录'
    )

    # ===== 异常排查（定位故障原因）=====
    message = fields.Text(string='摘要', help='简短的执行结果说明')
    detail = fields.Text(
        string='详细日志',
        help='完整报错堆栈、API请求/响应内容，用于开发排查'
    )
    request_params = fields.Text(
        string='API请求参数',
        help='调用第三方汇率接口的请求参数'
    )
    response_content = fields.Text(
        string='API响应内容',
        help='第三方汇率接口返回的原始内容'
    )

    display_name = fields.Char(
        string='名称',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('provider_id', 'create_date', 'state')
    def _compute_display_name(self):
        for rec in self:
            provider_name = rec.provider_id.name or 'Unknown'
            date_str = rec.create_date.strftime('%Y-%m-%d %H:%M') if rec.create_date else ''
            state_label = dict(self._fields['state'].selection).get(rec.state, '')
            rec.display_name = f'[{state_label}] {provider_name} - {date_str}'

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                rec.duration_ms = int((rec.end_time - rec.start_time).total_seconds() * 1000)
            else:
                rec.duration_ms = 0

    # ===== 统一日志写入方法，所有更新入口都调用这个 =====
    @api.model
    def log_update(self, provider, trigger_type='manual'):
        """统一的汇率更新日志写入方法，覆盖手动、cron、API所有入口"""
        start_time = fields.Datetime.now()
        # 1. 先创建「运行中」日志，就算进程崩了也能查到未完成的更新
        log = self.create({
            'provider_id': provider.id,
            'company_id': provider.company_id.id,
            'trigger_type': trigger_type,
            'state': 'running',
            'start_time': start_time,
            'message': f'开始执行{provider.name}的汇率更新'
        })

        try:
            # 2. 记录API请求参数
            today = fields.Date.context_today(self)
            log.write({
                'request_params': f'date_from={today}, date_to={today}, newest_only=True'
            })

            # 3. 调用OCA原生更新逻辑
            rate_ids = provider._update(today, today, newest_only=True)

            # 4. 更新成功日志
            currencies = ','.join(rate_ids.mapped('currency_id.name'))
            log.write({
                'state': 'success',
                'end_time': fields.Datetime.now(),
                'rates_count': len(rate_ids),
                'updated_currencies': currencies,
                'rate_ids': [(6, 0, rate_ids.ids)],
                'message': f'成功更新{len(rate_ids)}笔汇率，涉及币种：{currencies}'
            })
            return rate_ids

        except Exception as e:
            # 5. 更新失败日志，存完整堆栈和上下文
            log.write({
                'state': 'failed',
                'end_time': fields.Datetime.now(),
                'message': f'更新失败：{str(e)}',
                'detail': traceback.format_exc()  # 完整报错堆栈，开发直接看就能定位问题
            })
            raise  # 把异常抛回给OCA原生逻辑，不影响原有流程