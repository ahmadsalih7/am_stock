# -*- coding: utf-8 -*-
{
    'name': "AM stock",
    'author': "Ahmad Salih",
    'category': 'Accounting',
    'version': '0.1',

    'depends': ['base',
                'mail'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/menu_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True
}
