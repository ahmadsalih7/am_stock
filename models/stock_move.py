# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID


class StockMove(models.Model):
    _name = "stock.move"
    _description = "Stock Move"
    _order = 'sequence, id'

    name = fields.Char('Description', index=True, required=True)
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
    product_qty = fields.Float('Real Quantity')
    product_uom_qty = fields.Float('Demand', default=0.0, required=True, states={'done': [('readonly', True)]})
    picking_id = fields.Many2one('am_stock.picking', 'Transfer Reference', states={'done': [('readonly', True)]})
