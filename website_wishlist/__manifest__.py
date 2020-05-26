# -*- coding: utf-8 -*-
#################################################################################
#
# Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
# See LICENSE file for full copyright and licensing details.
#################################################################################

{
  "name"                 :  "Website Product Wishlist",
  "summary"              :  "Add products to your wishlist for later purchase.",
  "category"             :  "Website",
  "version"              :  "1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Product-Wishlist.html",
  "description"          :  """http://webkul.com/blog/odoo-product-wishlist/""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_wishlist&version=12.0",
  "depends"              :  [
                             'website_sale','sale','sale_management',
                            ],
  "data"                 :  [
                              'security/ir.model.access.csv',
                              'views/templates.xml',
                              'views/wk_wishlist.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  39,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}