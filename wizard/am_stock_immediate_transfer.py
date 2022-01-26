# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _name = 'am_stock.immediate.transfer'
    _description = 'Immediate Transfer'

    pick_ids = fields.Many2many('am_stock.picking', 'am_stock_picking_transfer_rel')

    def process(self):
        pass