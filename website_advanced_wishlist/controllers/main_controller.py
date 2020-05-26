# -*- coding: utf-8 -*-
#################################################################################
#
# Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
# See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_wishlist.controllers.main import WebsiteWishlist
import logging
_logger = logging.getLogger(__name__)


class WebsiteWishlists(WebsiteSale):
   
    def get_attribute_values_dict(self, product):
        variant_attribute_values_dict = dict()
        for value_id in product.attribute_value_ids:
            variant_attribute_values_dict[value_id.attribute_id.id] = value_id.id
        return variant_attribute_values_dict
    def sort_wishlist(self,wishlists):
        self.sorted_wishlists = []
        for wishlist in wishlists:
            if wishlist.is_default:
                self.sorted_wishlists.insert(0,wishlist)
            else:
                self.sorted_wishlists.append(wishlist)
        return self.sorted_wishlists

    @http.route('/shop/default/wishlist/', type="json", auth="public", website=True)
    def get_default_wishlist(self):
        default_wishlist = request.env['wishlist.name'].get_default_wishlist()
        params = request.env['ir.config_parameter'].sudo()
        add_to_wishlist_action = params.get_param(('website_wishlist.add_to_wishlist_action'), default=False)
        if not add_to_wishlist_action:
            add_to_wishlist_action="show"
        wishlist_product_records = request.env['website.wishlist'].current().mapped('product_id')
        if default_wishlist:
            data={
                    'name_id':default_wishlist.id,
                    'add_to_wishlist_action':add_to_wishlist_action,
                }
            return data
        else:
            wishlists=request.env['wishlist.name'].get_wishlists()
            if wishlists:
                default_wishlist = wishlists[0]
                default_wishlist.write({'is_default':True})
            return {

                    'name_id':default_wishlist.id if default_wishlist else False,
                    'add_to_wishlist_action':add_to_wishlist_action,
            }

    @http.route('/get/popover/wislists/', type="http", auth="public", website=True)
    def get_popover_wishlists(self,product_id,*args):
        wishlists =  request.env['wishlist.name'].get_wishlists().sorted(key=lambda x: product_id in [product.id for product in x.wishlist_line_ids]==True)
        if wishlists:
            sorted_wishlists=[]
            for wishlist in wishlists:
                if int(product_id) in [ w_record.product_id.id for w_record in wishlist.wishlist_line_ids]:
                    sorted_wishlists.insert(0,wishlist)
                else:
                    sorted_wishlists.append(wishlist)
            return request.render("website_advanced_wishlist.create_wishlists", {'wishlists':sorted_wishlists,'product_id':product_id})
        return False

    @http.route(['/shop/create/wislist/'], type='json', auth="public", website=True)
    def create_wishlist(self, name, make_it_default,product_id, **post):
        added =request.env['wishlist.name'].create_new_wishlist(name)
        if added:
            wishlists =  request.env['wishlist.name'].get_wishlists()
            if wishlists:
                data={
                    'html':request.env['ir.ui.view'].render_template("website_advanced_wishlist.create_wishlists", {'wishlists':wishlists,'product_id':product_id}),
                    'name_id':added.id,
                }
                if make_it_default:
                    self.set_as_default_wishlist(added.id)
                return data 
            return True
            
        return False

    @http.route('/remove/wishlist/<model("wishlist.name"):wishlist>/', type='json', auth='public', website=True)
    def remove_wishlist(self,wishlist, *args, **kwargs):
        b=False
        d_wishlist_id=False
        if wishlist.is_default:
            b=True
        res = wishlist.unlink()
        if b:
            wishlist=request.env['wishlist.name'].search([],limit=1)
            if wishlist:
                wishlist.write({'is_default':True})
                d_wishlist_id=wishlist.id
        return {
            'res':res,
            'name_id':d_wishlist_id
        }

    @http.route(['/save/wishlist/<model("wishlist.name"):wishlist>/',], type='json', auth="public", website=True)
    def save_wishlist(self,wishlist,name, **post):
        res = wishlist.write({'name':name})
        return res 

    @http.route('/wishlist/set_as_default/', type='json', auth='public', website=True)
    def set_as_default_wishlist(self, name_id, **kwargs):
        wishlist = request.env['wishlist.name'].get_default_wishlist()
        if wishlist:
            wishlist.write({'is_default':False})
        
        wishlist = request.env['wishlist.name'].search([('id','=',name_id)])
        if wishlist:
            wishlist.write({'is_default':True})
            return name_id     
        return False

    @http.route('/shop/wishlist/tabview/', type="http", auth="public", website=True)
    def get_wishlist_tab_view(self ,**kwa):
        d_wishlist =request.env['wishlist.name'].get_default_wishlist()
        d_wishlist_id = d_wishlist.id if d_wishlist else False
        if not d_wishlist_id:
            d_wishlist_id=self.get_default_wishlist().get('name_id')

        values = {
            'selected_wishlist_id':d_wishlist_id,
            'wishlists':self.sort_wishlist(request.env['wishlist.name'].get_wishlists()),
            'get_attribute_exclusions': self._get_attribute_exclusions,
            'get_attribute_values_dict': self.get_attribute_values_dict,
            }
        return request.render("website_advanced_wishlist.wishlists_tab_view", values)

    @http.route('/shop/wishlist/product/move', type="json", auth="public", website=True)
    def move_to_wishlist(self, product_id,source_id,target_id,**kwa):
        if not request.env['website.wishlist'].get_wishlist_product(int(target_id),int(product_id)):
            record = request.env['website.wishlist'].get_wishlist_product(int(source_id),int(product_id))
            if record:
                record.write({"wishlist_name_id":target_id})
                return True
            return False
        else:
            return False

    @http.route(['/wishlists/'], type='http', auth="public", website=True)
    def wishlists(self, name_id=-1,**post):        
        if not request.env['wishlist.name'].search([('id','=',int(name_id))]):       
            wishlist = request.env['wishlist.name'].get_default_wishlist()
            if wishlist:
                name_id=wishlist.id
            else:
                name_id= self.get_default_wishlist().get('name_id')

        values = {
        'selected_wishlist_id':int(name_id),
        'wishlists':self.sort_wishlist(request.env['wishlist.name'].get_wishlists()),
        'get_attribute_exclusions': self._get_attribute_exclusions,
        'get_attribute_values_dict': self.get_attribute_values_dict,
        }
        return http.request.render("website_advanced_wishlist.wishlists_page", values)
        
    @http.route(['/shop/wishlist/cart/move/<model("wishlist.name"):wishlist>/'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def move_wishlist_to_cart(self, wishlist, line_id=None, add_qty=1, set_qty=None, display=True):
        products = wishlist.wishlist_line_ids
        order_list=[]
        for product in products:
            product_id = product.product_id.id
            value={}
            order = request.website.sale_get_order(force_create=1)
            value = order._cart_update(product_id=int(product_id), line_id=line_id, add_qty=add_qty, set_qty=set_qty)
            if not display:
                return None
            value['cart_quantity'] = order.cart_quantity
            order_list.append(value)
            
            product.unlink()             
        return order_list

class NewWebsiteWishlist(WebsiteWishlist):

    @http.route('/wishlist/add_to_wishlist', type='json', auth='public', website=True)
    def wk_add_to_wishlist(self, product,name_id, *args, **kwargs):
        res = request.env['website.wishlist'].add_product(int(product),int(name_id))
        # _logger.info("....................%r................%r........%r./..........",name_id,product,res)
        if res:
            total_products_count = len(request.env['wishlist.name'].search([('id','=',name_id)]).wishlist_line_ids)
            return total_products_count
        return False    

    @http.route('/wishlist/remove_from_wishlist/', type='json', auth='public', website=True)
    def wk_remove_from_wishlist(self, product_id, name_id, **kwargs):
        # _logger.info("....................%r................%r...........",name_id,product_id)
        res = request.env['website.wishlist'].remove_from_wishlist(int(name_id),int(product_id))
        # if res:
        total_products_count = len(request.env['wishlist.name'].search([('id','=',name_id)]).wishlist_line_ids)
        return total_products_count
        # return False

    
