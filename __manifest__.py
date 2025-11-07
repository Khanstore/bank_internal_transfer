# -*- coding: utf-8 -*-
{
    'name': 'Bank Internal Transfer',
    'version': '18.0.0.2',
    'author': 'SM Ashraf',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/internal_transfer_wizard_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}
