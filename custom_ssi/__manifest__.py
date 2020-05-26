
# -*- coding: utf-8 -*-
{
    'name': "SSI Custom Mods",


    'author': "Kristenn - SSI",
    'website': "http://ssibtr.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',
    'auto_install': True,

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'website_sale',
        'sale_enterprise',
        'delivery',
    ],

    # always loaded
    'data': [
        'views/assets.xml',
        'views/restore.xml',
        'views/ssi_sales_order.xml'
#         'views/ssi_sales_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
