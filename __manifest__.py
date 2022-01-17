# -*- coding: utf-8 -*-
{
    'name': "am_stock",
    'author': "Ahmad Salih",
    'category': 'Accounting',
    'version': '0.1',

    'depends': ['base'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True
}
