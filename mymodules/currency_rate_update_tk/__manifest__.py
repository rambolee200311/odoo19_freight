{
    'name': 'Currency Rate Update TK Extension',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'TK Freight 业务适配层：币别配置、审计日志、波动拦截',
    'depends': [
        'currency_rate_update',
        'tk_freight',
    ],
    'data': [
        'views/currency_rate_provider_views.xml',
        'wizards/update_rates_wizard.xml',
        'data/ir_cron.xml',
        'views/currency_rate_update_log_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
