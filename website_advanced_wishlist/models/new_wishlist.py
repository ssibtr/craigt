# -*- coding: utf-8 -*-
#################################################################################
#
# Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
# See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields,models,api

class NewWishlist(models.Model):
    _name = "wishlist.name"
    _order = " id desc ,wishlist_line_ids desc "

    name = fields.Char(string = "Name",required = True)
    partner_id = fields.Many2one(comodel_name = "res.partner", string = "Partner")
    wishlist_line_ids = fields.One2many(comodel_name ="website.wishlist" ,inverse_name = "wishlist_name_id")
    user_id = fields.Integer(string = "User id")
    is_default =fields.Boolean(string="Default",default=False ,readonly=True ) 
    
    @api.model
    def get_default_wishlist(self):
        User = self.env.user
        if User.partner_id:
            default_wish_list = self.search(['|',('partner_id','=',User.partner_id.id),('user_id','=',User.id),('is_default','=',True)])
            if default_wish_list:
                return default_wish_list
            else:
                return False
    @api.model
    def get_wishlists(self):
        User =  self.env.user
        return self.search(['|',('partner_id','=',User.partner_id.id),('user_id','=',User.id)])

    @api.model
    def create_new_wishlist(self,name ):
        User = self.env.user
        default_wishlist = False if self.get_default_wishlist() else True
        if User.partner_id:
            vals = {
                'name': name,
                'partner_id':User.partner_id.id,
                'user_id':User.id,
                'is_default':default_wishlist,
            }

        if 'name' in vals and  'partner_id' in vals and 'user_id' in vals:
            check = self.search([('name','=',vals['name']),('partner_id','=',vals['partner_id']),('user_id','=',vals['user_id'])])
            if check:
                return False

        return super(NewWishlist, self).create(vals)   
