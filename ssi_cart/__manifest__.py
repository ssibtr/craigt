# -*- coding: utf-8 -*-
# Copyright 2019 Openworx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'SSI CART',
    'category': 'Saved Cart Management',
    'summary': 'View saved cart in user portal',
    'version': '1.0',
    'license': 'AGPL-3',
    'author': 'SSIBTR',
    'description': """
        View saved cart in user portal
    """,
    'depends': [
        'portal',
    ],
    'data': [
        'views/templates.xml',
        # 'views/restore.xml',
        'views/payment_cart.xml',
        'views/portal_home.xml',
        'views/portal_layout.xml',
        # 'views/portal_template.xml',
        'views/sale_form_cart.xml',
    ],
    'installable': True,
}
