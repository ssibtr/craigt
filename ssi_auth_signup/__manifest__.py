{
    'name': 'SSI Custom Auth Signup Form',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'summary': 'Auth signup form custom fields for Address info and tax exemption',
    'description': """
        This module add addres info, phone number and tax exempt statuis to auth sign up
        * Address
        * Phone #
        * Tax Exempt
    """,
    'sequence': 1,
    'author': 'Systems Services, Inc.',
    'website': 'http://ssibtr.com',
    'depends': ['auth_signup'],
    'data': [
        'views/ssi_auth_signup_custom_views.xml',
    ],
    'qweb': [],
    'css': [],
    'js': [],
    'images': [],
    'demo': [],
    'category': 'Website',
    'version': '1.0',
    'installable': True,
    'auto_install': False,
    'application': True,
}
