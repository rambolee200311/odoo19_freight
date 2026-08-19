from odoo import models, fields, api
import traceback
import logging
import xml.etree.ElementTree as ET  # 新增，用来解析XML看内容
from datetime import datetime,time
from dateutil.relativedelta import relativedelta 
_logger = logging.getLogger(__name__)

class CurrencyRateProvider(models.Model):
    _inherit = 'res.currency.rate.provider'

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
    # 在字段定义区域加这一行
    log_ids = fields.One2many(
        comodel_name='currency.rate.update.log',
        inverse_name='provider_id',
        string='更新日志',
        readonly=True,
        order='create_date desc',
    )

    # 【新增】重写_obtain_rates，记录ECB返回的原始数据
    def _obtain_rates_old1(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != 'ECB':
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        
        # 【日志4：记录ECB请求参数】
        _logger.error(f"""
        ===== 请求ECB接口 =====
        URL参数：
        base_currency={base_currency}
        请求的币种：{currencies}
        日期范围：{date_from}~{date_to}
        """)
        
        # 调用OCA原生的ECB请求逻辑
        content = super()._obtain_rates(base_currency, currencies, date_from, date_to)
        
        # 【日志5：记录ECB返回的原始数据】
        _logger.error(f"""
        ===== ECB返回原始数据 =====
        返回日期列表：{list(content.keys())}
        8月17日的数据：{content.get('2026-08-17', '不存在')}
        请求的币种在返回里的存在情况：{[c in content.get('2026-08-17', {}) for c in currencies]}
        完整返回内容前2000字符：{str(content)[:2000]}
        """)
        
        return content

    def _update(self, date_from, date_to, newest_only=False):
        log_model = self.env['currency.rate.update.log']
        # 拿到res.currency.rate的模型类（不是记录集实例）
        RateModel = self.env.registry['res.currency.rate']
        
        for provider in self:
            start_time = fields.Datetime.now()
            detail_lines = []  # 逐条明细日志
            affected_ids = []  # 本次影响的记录ID

            # ===== 1. 保存原始模型方法 =====
            original_create = RateModel.create
            original_write = RateModel.write

            # ===== 2. 包装create方法：每新建一条汇率就记一条日志 =====
            @api.model
            def patched_create(self_cls, vals_list, *args, **kwargs):
                """拦截所有create调用，逐条记录"""
                # 兼容OCA传单条dict或列表的情况
                if isinstance(vals_list, dict):
                    vals_list = [vals_list]
                
                for vals in vals_list:
                    # 只记录当前服务商、目标日期范围内的汇率
                    if (vals.get('provider_id') == provider.id and 
                        date_from <= vals.get('name') <= date_to):
                        detail_lines.append({
                            'action': 'create',
                            'currency_id': vals.get('currency_id'),
                            'date': vals.get('name'),
                            'rate': vals.get('rate'),
                            'provider_id': vals.get('provider_id'),
                        })
                
                # 调用原始create方法，注意第一个参数是模型类self_cls
                records = original_create(self_cls, vals_list, *args, **kwargs)
                affected_ids.extend(records.ids)
                return records

            # ===== 3. 包装write方法：每更新一条汇率就记一条日志 =====
            def patched_write(self_recs, vals, *args, **kwargs):
                """拦截所有write调用，逐条记录"""
                for rec in self_recs:
                    # 只记录当前服务商、目标日期范围内的汇率
                    if (rec.provider_id.id == provider.id and 
                        date_from <= rec.name <= date_to):
                        detail_lines.append({
                            'action': 'write',
                            'record_id': rec.id,
                            'currency_id': rec.currency_id.id,
                            'date': rec.name,
                            'rate_before': rec.rate,
                            'rate_after': vals.get('rate', rec.rate),
                        })
                        affected_ids.append(rec.id)
                
                # 调用原始write方法，第一个参数是记录集self_recs
                return original_write(self_recs, vals, *args, **kwargs)

            try:
                # ===== 4. 临时替换模型类的方法 =====
                RateModel.create = patched_create
                RateModel.write = patched_write

                # ===== 5. 调用OCA原生更新逻辑，参数完全透传 =====
                super()._update(date_from, date_to, newest_only=newest_only)

            finally:
                # ===== 6. 无论成功失败，必须还原原始方法，避免污染后续操作 =====
                RateModel.create = original_create
                RateModel.write = original_write

            # ===== 7. 整理日志明细，去重记录ID =====
            unique_ids = list(dict.fromkeys(affected_ids))  # 保序去重
            detail_text = ""
            for i, line in enumerate(detail_lines, 1):
                if line['action'] == 'create':
                    detail_text += (
                        f"[{i}] CREATE | 币种ID={line['currency_id']} | "
                        f"日期={line['date']} | 汇率={line['rate']}\n"
                    )
                else:
                    detail_text += (
                        f"[{i}] WRITE  | 记录ID={line['record_id']} | "
                        f"币种ID={line['currency_id']} | 日期={line['date']} | "
                        f"汇率 {line['rate_before']} → {line['rate_after']}\n"
                    )

            # ===== 8. 写审计日志 =====
            log_model.create({
                'provider_id': provider.id,
                'trigger_type': self.env.context.get('trigger_type', 'manual'),
                'state': 'success' if detail_lines else 'success',
                'rates_count': len(detail_lines),
                'rate_ids': [(6, 0, unique_ids)],
                'start_time': start_time,
                'end_time': fields.Datetime.now(),
                'message': f'本次逐条处理{len(detail_lines)}笔汇率',
                'detail': detail_text or '无明细（目标记录均已存在且值未变化）'
            })

            # ===== 9. 同步更新服务商审计字段 =====
            if unique_ids:
                rates = self.env['res.currency.rate'].browse(unique_ids)
                provider.last_rate = rates.sorted('name', reverse=True)[0].rate
            provider.last_update = fields.Datetime.now()
            provider.update_status = 'success'

            return self.env['res.currency.rate'].browse(unique_ids)

    @api.model
    def _scheduled_update(self):
        """重写Cron定时更新逻辑，增加日志和过滤规则"""
        _logger.info("===== 开始执行汇率定时更新任务 =====")
        today = fields.Date.context_today(self)
        yesterday = today - relativedelta(days=1)  # ECB只发布前一天的数据

        # 1. 只筛选：开启自动更新、激活、且勾选了纳入自动更新的服务商
        providers = self.search([
            ('company_id.currency_rates_autoupdate', '=', True),
            ('active', '=', True),
            ('active_for_auto', '=', True),  # 你之前加的控制字段终于生效了
            '|', ('next_run', '<=', today), ('daily', '=', True)
        ])

        if not providers:
            _logger.info("没有符合条件的汇率服务商需要更新，任务结束")
            return

        provider_names = ", ".join(providers.mapped('name'))
        _logger.info(f"本次定时更新将处理以下服务商：{provider_names}")

        success_count = 0
        fail_count = 0

        for provider in providers.with_context(trigger_type='cron'):  # 2. 标记Cron触发
            try:
                # 3. 日期范围计算（复用OCA原生逻辑，仅针对ECB做适配）
                if provider.last_successful_run:
                    date_from = provider.last_successful_run + relativedelta(days=1)
                else:
                    date_from = provider.next_run - provider._get_next_run_period()

                newest_only = True
                date_to = provider.next_run

                # 4. 针对ECB的特殊适配：结束日期设为昨天，避免拉不到未发布的数据
                if provider.service == 'ECB':
                    date_to = yesterday
                    newest_only = False  # ECB的历史数据要拉全量，不是只拉最新
                    _logger.debug(f"ECB服务商调整日期范围：{date_from} ~ {date_to}")

                # 5. 如果是每日更新，拉取到今天的数据
                if provider.daily:
                    newest_only = False
                    date_to = today

                # 6. 调用更新逻辑，日志会自动写入你已有的log表
                provider._update(date_from, date_to, newest_only=newest_only)
                success_count += 1
                _logger.info(f"服务商[{provider.name}]定时更新成功")

            except Exception as e:
                fail_count += 1
                _logger.error(f"服务商[{provider.name}]定时更新失败：{str(e)}", exc_info=True)
                # 异常日志已经在你重写的_update方法里写了，这里只需要记录Cron级别的汇总
                continue

        _logger.info(
            f"===== 汇率定时更新任务完成：成功{success_count}个，失败{fail_count}个 ====="
        )        