# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields,models,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    action=fields.Selection([
        ('default', 'Add to default wishlist'),
        ('show', 'Show all available wishlists'),],readonly=False)
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        action=params.get_param(('website_wishlist.add_to_wishlist_action'), default=False)
        if not action:
            action="show"
    
        res.update(action = action,)
        return res
    
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('website_wishlist.add_to_wishlist_action', self.action)
        super(ResConfigSettings, self).set_values()
        