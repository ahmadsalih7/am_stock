# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Warehouse(models.Model):
    _name = "am_stock.warehouse"
    _description = "Warehouse"
    _order = 'sequence,id'
    _check_company_auto = True

    name = fields.Char('Warehouse', index=True, required=True, default=lambda self: self.env.company.name)
    active = fields.Boolean('Active', default=True)
    code = fields.Char('Short Name', required=True, size=5, help="Short name used to identify your warehouse")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 index=True, readonly=True, required=True,
                                 help='The company is automatically set from your user preferences.')
    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id,
                                 check_company=True)
    out_type_id = fields.Many2one('am_stock.picking.type', 'Out Type', check_company=True)
    in_type_id = fields.Many2one('am_stock.picking.type', 'In Type', check_company=True)

    @api.model
    def create(self, vals):
        # actually create WH
        warehouse = super(Warehouse, self).create(vals)
        # create sequences and operation types
        new_vals = warehouse._create_sequence_and_picking_types()
        warehouse.write(new_vals)
        return warehouse

    def _get_sequence_values(self):
        return {
            'in_type_id': {
                'name': self.name + ' ' + _('Sequence in'),
                'prefix': self.code + '/IN/', 'padding': 5,
                'company_id': self.company_id.id,
            },
            'out_type_id': {
                'name': self.name + ' ' + _('Sequence out'),
                'prefix': self.code + '/OUT/', 'padding': 5,
                'company_id': self.company_id.id,
            },
        }

    def _get_picking_type_create_values(self):
        return {
            'in_type_id': {
                'name': _('Receipts'),
                'code': 'incoming',
                'barcode': self.code.replace(" ", "").upper() + "-RECEIPTS",
                'sequence_code': 'IN',
                'company_id': self.company_id.id,
            }, 'out_type_id': {
                'name': _('Delivery Orders'),
                'code': 'outgoing',
                'barcode': self.code.replace(" ", "").upper() + "-DELIVERY",
                'sequence_code': 'OUT',
                'company_id': self.company_id.id,
            }}

    def _create_sequence_and_picking_types(self):
        IrSequenceSudo = self.env['ir.sequence'].sudo()
        PickingType = self.env['am_stock.picking.type']

        warehouse_data = {}
        create_data = self._get_picking_type_create_values()
        sequence_data = self._get_sequence_values()

        for picking_type, picking_type_values in create_data.items():
            sequence = IrSequenceSudo.create(sequence_data[picking_type])
            picking_type_values.update(warehouse_id=self.id, sequence_id=sequence.id)
            warehouse_data[picking_type] = PickingType.create(picking_type_values).id

        return warehouse_data
