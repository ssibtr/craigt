# -*- coding: utf-8 -*-

#################################################################################
# Systems Services, Inc.
# Desc: To extend maintenance module to add fields to equipment
#################################################################################

{
    'name': 'SSI Leads',
    'summary': "Adds Leads module to Odoo.",
    'version': '1.0.1',
    'category': 'SSI',
    'author': 'Systems Services, Inc. '
              'Kristenn Quemener ',
    'website': 'https://ssibtr.com',
    "depends":  [
        'base',
        'crm',
    ],
    'data': [
        'views/leads.xml',
        'views/contact.xml',
    ],
    'installable': True,
    'application': True,
}
