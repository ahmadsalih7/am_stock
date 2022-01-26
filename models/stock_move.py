# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID


class StockMove(models.Model):
    _name = "am_stock.move"
    _description = "Stock Move"

    name = fields.Char('Description', index=True, required=True)
    origin = fields.Char("Source Document")
    create_date = fields.Datetime('Creation Date', index=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 index=True, required=True)
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True)
    product_id = fields.Many2one('my_product.template', 'Product', check_company=True,
                                 domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 index=True, required=True,
                                 states={'done': [('readonly', True)]})
    warehouse_id = fields.Many2one('am_stock.warehouse', 'Warehouse',
                                   help="Technical field depicting the warehouse to consider for the route selection on the next procurement (if any).")
    quantity_done = fields.Float('Quantity Done')
    product_quantity = fields.Float('Demand', default=0.0, required=True, states={'done': [('readonly', True)]})
    picking_id = fields.Many2one('am_stock.picking', 'Transfer Reference', states={'done': [('readonly', True)]})
    picking_type_id = fields.Many2one('am_stock.picking.type', 'Operation Type', check_company=True)

    def _action_confirm(self):
        ''' Change moves state to confirmed '''
        for move in self:
            move.write({'state': 'confirmed'})

    def _action_assign(self):
        ''' Change moves state to assigned '''
        for move in self:
            move.write({'state': 'assigned'})
