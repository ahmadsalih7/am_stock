# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Warehouse(models.Model):
    _name = "am_stock.warehouse"
    _description = "Warehouse"
    _order = 'sequence,id'
    _check_company_auto = True

    name = fields.Char('Warehouse', index=True, required=True, default=lambda self: self.env.company.name)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 index=True, readonly=True, required=True,
                                 help='The company is automatically set from your user preferences.')
    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id,
                                 check_company=True)
    code = fields.Char('Short Name', required=True, size=5, default='WH',
                       help="Short name used to identify your warehouse")
