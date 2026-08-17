# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

{
    'name': 'All in one Freight Management | Advance Freight | Transport Management',
    'description': """
        - Freight Management
        - Transport Management
        - Air, Land & Ocean Transport
    """,
    'summary': """
        All types of transportation management
    """,
    'version': '2.2.2',
    'author': 'TechKhedut Inc.',
    'category': 'services',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'website': "https://techkhedut.com",
    'depends': ['contacts',
                'base',
                'base_setup',
                'account',
                'product',
                'web',
                'fleet',
                'mail',
                'board',
                'calendar',
                'sale_management',
                'stock',
                'website',
                'crm',
                'portal',
                'hr'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        # Data
        'data/freight_data.xml',
        'data/freight_paperformat.xml',
        # wizard
        'wizard/shipment_invoice_view.xml',
        # Views
        'views/asset.xml',
        'views/freight_shipment_view.xml',
        'views/freight_statement_view.xml',
        'views/freight_statement_wizard_view.xml',
        'views/freight_configuration.xml',
        'views/booking_view.xml',
        'views/freight_templates.xml',
        'views/stages_view.xml',
        'views/freight_quotation_view.xml',
        'views/res_config_view.xml',
        'views/freight_port.xml',
        'views/freight_crm_inherit_view.xml',
        'views/stock_picking_views.xml',
        'views/shipment_package_line_views.xml',
        'views/freight_route_views.xml',
        # Report
        'report/freight_details_report.xml',
        'report/cmr_bill_land.xml',
        'report/bill_of_landing_report.xml',
        'report/shipping_instruction_report.xml',
        'report/airway_bill_report.xml',
        'report/freight_booking_form.xml',
        'report/freight_quotation_report.xml',
        'report/shipment_bill_qweb_report.xml',
        'report/waybill_land_qweb_report.xml',
        'report/customer_statement_report.xml',
        # Menu
        'views/menus.xml',
        # Mail Template
        'data/quot_booking_mail_template.xml',
        'data/booking_shipment_mail_template.xml',
        'data/quot_sent_mail_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tk_freight/static/src/xml/template.xml',
            'tk_freight/static/src/xml/template_CN.xml',
            'tk_freight/static/src/css/style.scss',
            'tk_freight/static/src/js/lib/apexcharts.js',
            # 'tk_freight/static/src/js/freight.js',
            'tk_freight/static/src/js/dashboard.js',
        ],
        'web.assets_frontend': [
            'tk_freight/static/src/css/freight.css',
            'tk_freight/static/src/css/dashboard.css',
            'tk_freight/static/src/css/dashboard_CN.css',
            'tk_freight/static/src/js/script.js',
        ],
    },
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'translate': True,
    'auto_install': False,
    'price': 175.00,
    'currency': 'USD',
    'license': 'OPL-1',
}
