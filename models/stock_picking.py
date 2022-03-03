# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from collections import defaultdict
from ast import literal_eval
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


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

    count_picking_draft = fields.Integer(compute='_compute_picking_count')
    count_picking_ready = fields.Integer(compute='_compute_picking_count')
    count_picking = fields.Integer(compute='_compute_picking_count')
    count_picking_waiting = fields.Integer(compute='_compute_picking_count')
    count_picking_late = fields.Integer(compute='_compute_picking_count')

    def name_get(self):
        """ Show company beside type """
        result = []
        for rec in self:
            result.append((rec.id, f'{rec.company_id.name}: {rec.name}'))
        return result

    def _compute_picking_count(self):
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
        }
        for field in domains:
            data = self.env['am_stock.picking'].read_group(domains[field] +
                                                           [('state', 'not in', ('done', 'cancel')),
                                                            ('picking_type_id', 'in', self.ids)],
                                                           ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def _get_action(self, action_xmlid):
        action = self.env.ref(action_xmlid).read()[0]
        context = {
            'search_default_picking_type_id': [self.id],
        }
        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action

    def get_stock_picking_action_picking_type(self):
        return self._get_action('am_stock.action_stock_picking')

    def get_action_picking_tree_ready(self):
        return self._get_action('am_stock.action_picking_tree_ready')


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

    move_type = fields.Selection([
        ('direct', 'As soon as possible'), ('one', 'When all products are ready')], 'Shipping Policy',
        default='direct', required=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="It specifies goods to be deliver partially or all at once")
    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")

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
    move_lines = fields.One2many('am_stock.move', 'picking_id', string="Stock moves")

    @api.model
    def create(self, vals):
        sequence = self.env['am_stock.picking.type'].browse(vals['picking_type_id']).sequence_id
        if vals.get('name', '/') == '/':
            if sequence:
                vals['name'] = sequence.next_by_id()
        return super(Picking, self).create(vals)

    @api.depends('move_lines.state', 'move_lines.picking_id')
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

    @api.depends('move_lines.date_expected')
    def _compute_scheduled_date(self):
        for picking in self:
            if picking.move_type == 'direct':
                picking.scheduled_date = min(picking.move_lines.mapped('date_expected') or [fields.Datetime.now()])
            else:
                picking.scheduled_date = max(picking.move_lines.mapped('date_expected') or [fields.Datetime.now()])

    def _set_scheduled_date(self):
        for picking in self:
            if picking.state in ('done', 'cancel'):
                raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date_expected': picking.scheduled_date})

    def button_validate(self):
        no_quantities_done = all(move_line.quantity_done == 0.0 for move_line in
                                 self.move_lines.filtered(lambda m: m.state not in ('done', 'cancel')))
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

    def action_done(self):
        self.write({'date_done': fields.Datetime.now()})
        self.write({'state': 'done'})
