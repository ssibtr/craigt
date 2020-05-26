# -*- coding: utf-8 -*-
from odoo import fields,models,api

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    template_id = fields.Many2one('mail.template', string='Email Template',
                                  domain="[('model','=','sale.order')]",
                                  default=lambda self: self.env.ref('sale.email_template_edi_sale'),
                                  required=True)
    template_email = fields.Char(string='Email From', default='customerservice@teacherdirect.com')

