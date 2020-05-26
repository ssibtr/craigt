# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields,models,api
import logging
_logger = logging.getLogger(__name__)

class WishlistUpgradation(models.Model):
    _inherit = "website.wishlist"
    
    wishlist_name_id = fields.Many2one(comodel_name = "wishlist.name", string = "Wishlist Name", ondelete='cascade')
    
    @api.model
    def add_product(self,product_id,name_id):
        User = self.env.user
        
        if User.partner_id:
            vals = {
                'product_id': product_id,
                'partner_id':User.partner_id.id,
                'user_id': User.id,
                'wishlist_name_id':name_id
            }
            
            return self.create(vals)
        return False 


    @api.model
    def current(self):
        """Get all wishlist items that belong to current user or session or current default wishlist. """
        return self.search([("partner_id", "=", self.env.user.partner_id.id)])

    @api.model
    def remove_from_wishlist(self, name_id ,product_id):
        User = self.env.user
        if User.partner_id:
            wishlist_line_obj = self.search(['&',('product_id','=',int(product_id)),('wishlist_name_id','=',int(name_id))])
            if wishlist_line_obj:
                wishlist_line_obj.sudo().unlink()
                return True          
        return False

    
    @api.model
    def get_wishlist_product(self,source_id,product_id):
        User = self.env.user
        if User.partner_id:
            products = self.search(['&',('wishlist_name_id','=',source_id),('product_id','=',product_id)])
            return products
            
        return False
