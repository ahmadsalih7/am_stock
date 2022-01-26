# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockImmediateTransfer(models.TransientModel):
    _name = 'am_stock.immediate.transfer'
    _description = 'Immediate Transfer'

    pick_ids = fields.Many2many('am_stock.picking', 'am_stock_picking_transfer_rel')

    def process(self):
        pick_to_do = self.env['am_stock.picking']
        for picking in self.pick_ids:
            for move in picking.move_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                move.quantity_done = move.product_quantity
            pick_to_do |= picking
        if pick_to_do:
            pick_to_do.action_done()
