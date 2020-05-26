
# -*- coding: utf-8 -*-
{
    'name': "SSI Website Filter",


    'author': "Chad - SSI",
    'website': "http://ssibtr.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'SSI',
    'version': '1.0',
    'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': [
        'website',
        'website_sale',
    ],
    # always loaded
    # 'data': [
        # 'report/back_stock_report_views.xml',
    # ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
