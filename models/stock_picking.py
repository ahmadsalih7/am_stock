# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from collections import defaultdict


class PickingType(models.Model):
    _name = "am_stock.picking.type"
    _description = "Picking Type"
    _check_company_auto = True

    name = fields.Char('Operation Type', required=True)
    code = fields.Selection([('incoming', 'Receipt'), ('outgoing', 'Delivery'), ('internal', 'Internal Transfer')],
                            'Type of Operation', required=True)
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence', check_company=True, copy=False)
    sequence_code = fields.Char('Code', required=True)
    barcode = fields.Char('Barcode', copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda s: s.env.company.id,
                                 index=True)
    warehouse_id = fields.Many2one('am_stock.warehouse', 'Warehouse', ondelete='cascade', check_company=True)

    def name_get(self):
        """ Show company beside type """
        result = []
        for rec in self:
            result.append((rec.id, f'{rec.company_id.name}: {rec.name}'))
        return result


class Picking(models.Model):
    _name = "am_stock.picking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Transfer"
    _order = "date desc, id asc"

    name = fields.Char('Reference', default='/', copy=False, index=True, readonly=True)
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonyl=True, compute='_compute_state', store=True)
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
    move_ids = fields.One2many('am_stock.move', 'picking_id', string="Stock moves")

    @api.model
    def create(self, vals):
        sequence = self.env['am_stock.picking.type'].browse(vals['picking_type_id']).sequence_id
        if vals.get('name', '/') == '/':
            if sequence:
                vals['name'] = sequence.next_by_id()
        return super(Picking, self).create(vals)

    @api.depends('move_ids.state', 'move_ids.picking_id')
    def _compute_state(self):
        picking_moves_state_map = defaultdict(dict)
        picking_move_lines = defaultdict(set)
        for move in self.env['am_stock.move'].search([('picking_id', 'in', self.ids)]):
            picking_id = move.picking_id
            move_state = move.state
            picking_moves_state_map[picking_id.id].update({
                'any_draft': picking_moves_state_map[picking_id.id].get('any_draft', False) or move_state == 'draft',
                'all_cancel': picking_moves_state_map[picking_id.id].get('all_cancel', True) and move_state == 'cancel',
                'all_cancel_done': picking_moves_state_map[picking_id.id].get('all_cancel_done',
                                                                              True) and move_state in (
                                       'cancel', 'done'),
            })
            picking_move_lines[picking_id.id].add(move.id)
        for picking in self:
            if not picking_moves_state_map[picking.id]:
                picking.state = 'draft'
            elif picking_moves_state_map[picking.id]['any_draft']:
                picking.state = 'draft'
            elif picking_moves_state_map[picking.id]['all_cancel']:
                picking.state = 'cancel'
            elif picking_moves_state_map[picking.id]['all_cancel_done']:
                picking.state = 'done'
            else:
                picking.state = 'assigned'

    def button_validate(self):
        no_quantities_done = all(move_line.quantity_done == 0.0 for move_line in
                                 self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        if no_quantities_done:
            view = self.env.ref('am_stock.view_immediate_transfer')
            wiz = self.env['am_stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'am_stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
