# -*- coding: utf-8 -*-
# from odoo import http


# class AmStock(http.Controller):
#     @http.route('/am_stock/am_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/am_stock/am_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('am_stock.listing', {
#             'root': '/am_stock/am_stock',
#             'objects': http.request.env['am_stock.am_stock'].search([]),
#         })

#     @http.route('/am_stock/am_stock/objects/<model("am_stock.am_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('am_stock.object', {
#             'object': obj
#         })
