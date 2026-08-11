# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPickingFreight(models.Model):
    """ Stock Picking Freight  """
    _inherit = 'stock.picking'

    freight_shipment_id = fields.Many2one('freight.shipment', copy=False)
    shipment_route_id = fields.Many2one('freight.route', copy=False)
