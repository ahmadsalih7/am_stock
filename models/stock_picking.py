# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _


class PickingType(models.Model):
    _name = "am_stock.picking.type"
    _description = "Picking Type"
    _order = 'sequence, id'
    _check_company_auto = True

    name = fields.Char('Operation Type', required=True)
    code = fields.Selection([('incoming', 'Receipt'), ('outgoing', 'Delivery'), ('internal', 'Internal Transfer')],
                            'Type of Operation', required=True)


class Picking(models.Model):
    _name = "am_stock.picking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transfer"
    _order = "date asc, id desc"

    name = fields.Char('Reference', default='/', copy=False, index=True, readonly=True)
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', readonyl=True)
    origin = fields.Char('Source Document', index=True,
                         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                         help="Reference of the document")
    date = fields.Datetime('Creation Date', default=fields.Datetime.now, index=True, tracking=True,
                           states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                           help="Creation Date, usually the time of the order")
    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=True,
                                help="Date at which the transfer has been processed or cancelled.")
    picking_type_id = fields.Many2one('am_stock.picking.type', 'Operation Type', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]})
    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='picking_type_id.code', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Contact",
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True)
    user_id = fields.Many2one('res.users', string="Responsible",
                              states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                              default=lambda self: self.env.user)
    move_ids = fields.One2many('stock.move', 'picking_id', string="Stock moves")
