# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class DashboardDetails(models.Model):
    """Freight Dashboard"""
    _name = 'dashboard.details'
    _description = __doc__

    name = fields.Char(translate=True)

    @api.model
    def get_freight_info(self):
        """get freight info"""
        fright_shipment = self.env['freight.shipment'].sudo()
        # Statics
        total_shipment = fright_shipment.search_count([])
        pending_quat = self.env['shipment.quotation'].sudo().search_count([('status', '=', 'q')])
        pending_booking = self.env['shipment.freight.booking'].search_count(
            [('state', '=', 'draft')])
        total_port = self.env['freight.port'].search_count([])
        shipper_count = self.env['res.partner'].sudo().search_count([('shipper', '=', True)])
        consignee_count = self.env['res.partner'].sudo().search_count([('consignee', '=', True)])
        # Shipment
        direct_count = fright_shipment.search_count([('operation', '=', 'direct')])
        house_count = fright_shipment.search_count([('operation', '=', 'house')])
        master_count = fright_shipment.search_count([('operation', '=', 'master')])
        air = fright_shipment.search_count([('transport', '=', 'air')])
        ocean = fright_shipment.search_count([('transport', '=', 'ocean')])
        land = fright_shipment.search_count([('transport', '=', 'land')])
        import_count = fright_shipment.search_count([('direction', '=', 'import')])
        export_count = fright_shipment.search_count([('direction', '=', 'export')])

        data = {
            # Statics
            'total_shipment': total_shipment,
            'pending_quat': pending_quat,
            'pending_booking': pending_booking,
            'total_port': total_port,
            'shipper_count': shipper_count,
            'consignee_count': consignee_count,
            # Shipment
            'direct_count': direct_count,
            'house_count': house_count,
            'master_count': master_count,
            'air': air,
            'ocean': ocean,
            'land': land,
            'freight_direction': [['Import', 'Export'], [import_count, export_count]],
            'shipment_stages': self.get_shipment_stages(),
            # Graph
            'get_shipment_month': self.get_shipment_month_type(),
            'move_type': self.get_move_type(),
            'top_shipper': self.get_top_shipper(),
            'top_consign': self.get_top_consignee(),
            'get_bill_invoice': self.get_freight_invoice_bills(),
        }
        return data

    # Shipment Stages
    def get_shipment_stages(self):
        """get shipment stages"""
        stages, shipment_counts, data = [], [], []
        stage_ids = self.env['freight.shipment.stages'].search(
            [], order='sequence asc')
        if not stage_ids:
            data = [[], []]
        for stg in stage_ids:
            shipment_data = self.env['freight.shipment'].sudo().search_count(
                [('stage_id', '=', stg.id)])
            shipment_counts.append(shipment_data)
            stages.append(stg.name)
        data = [stages, shipment_counts]
        return data

    # Top Shipper
    def get_top_shipper(self):
        """get top shipper"""
        shipper = {}
        groups = self.env['freight.shipment']._read_group([], ['shipper_id'],
                                                          ['shipper_id:count'], limit=10)
        for group in groups:
            shipper_id = group[0]
            if shipper_id:
                shipper_name = shipper_id.name
                shipper[shipper_name] = group[1]
        shipper = dict(
            sorted(shipper.items(), key=lambda x: x[1], reverse=True))
        return [list(shipper.keys()), list(shipper.values())]

    # Top Consignee
    def get_top_consignee(self):
        """Get top 5 consignees based on total amount"""
        consignee_ids = self.env['res.partner'].search([('consignee', '=', True)]).ids
        if not consignee_ids:
            return [[], []]
        AccountMove = self.env['account.move']
        groups = AccountMove._read_group(
            domain=[('partner_id', 'in', consignee_ids)],
            groupby=['partner_id'],
            aggregates=['amount_total:sum'],
            order='amount_total:sum DESC',
            limit=5,
        )
        partner_names, amounts = [], []
        for partner_id, total in groups:
            if partner_id:
                partner_names.append(partner_id.name)
                amounts.append(total)
        return [partner_names, amounts]

    # Move Type
    def get_move_type(self):
        """get move type"""
        move_type, counts, data = [], [], []
        move_types = self.env['freight.move.type'].search([])
        if not move_types:
            move_type, counts = [], []
        for type in move_types:
            rec = self.env['freight.shipment'].search_count(
                [('move_type', '=', type.id)])
            counts.append(rec)
            move_type.append(type.name)
        data = [move_type, counts]
        return data

    # Shipment Month
    def get_shipment_month(self):
        """get shipment month"""
        year = fields.Date.today().year
        year_str = str(year)
        return {
            '01/' + year_str: 0,
            '02/' + year_str: 0,
            '03/' + year_str: 0,
            '04/' + year_str: 0,
            '05/' + year_str: 0,
            '06/' + year_str: 0,
            '07/' + year_str: 0,
            '08/' + year_str: 0,
            '09/' + year_str: 0,
            '10/' + year_str: 0,
            '11/' + year_str: 0,
            '12/' + year_str: 0,
        }

    # Shipment Month Value
    def get_month_keys(self):
        """get month keys"""
        data = self.get_shipment_month()
        return list(data.keys())

    # Shipment By Month
    def get_shipment_month_type(self):
        """get shipment month type"""
        year = fields.Date.today().year
        air_dict = self.get_shipment_month()
        ocean_dict = self.get_shipment_month()
        land_dict = self.get_shipment_month()
        shipment = self.env['freight.shipment'].search([('create_datetime', '!=', False)])
        for data in shipment:
            if data.create_datetime.year == year:
                month_year = data.create_datetime.strftime("%m/%Y")
                if data.transport == 'air':
                    air_dict[month_year] = air_dict.get(month_year, 0) + 1
                elif data.transport == 'ocean':
                    ocean_dict[month_year] = ocean_dict.get(month_year, 0) + 1
                elif data.transport == 'land':
                    land_dict[month_year] = land_dict.get(month_year, 0) + 1
        month = self.get_month_keys()
        air = list(air_dict.values())
        ocean = list(ocean_dict.values())
        land = list(land_dict.values())
        return [month, air, ocean, land]

    # Freight Invoice Bill
    def get_freight_invoice_bills(self):
        """get freight invoice bills"""
        year = fields.Date.today().year
        bill_dict = self.get_shipment_month()
        invoice_dict = self.get_shipment_month()
        bill = self.env['account.move'].search([])
        for data in bill:
            if data.invoice_date and data.invoice_date.year == year and data.freight_operation_id:
                month_year = data.invoice_date.strftime("%m/%Y")

                if data.move_type == 'in_invoice':
                    bill_dict[month_year] = bill_dict.get(month_year, 0) + data.amount_total
                elif data.move_type == 'out_invoice':
                    invoice_dict[month_year] = invoice_dict.get(month_year, 0) + data.amount_total
        return [self.get_month_keys(), list(bill_dict.values()), list(invoice_dict.values())]
