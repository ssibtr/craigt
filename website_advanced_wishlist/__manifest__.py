# -*- coding: utf-8 -*-
#################################################################################
#
# Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
# See LICENSE file for full copyright and licensing details.
#################################################################################

{
  "name"                 :  "Website Advanced Wishlist",
  "summary"              :  "This module brings a brand new way to add product in your wishlist. Means user can create/manage multiple wishlist for different occassions.",
  "category"             :  "Website",
  "version"              :  "1.0.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/",
  "description"          :  """http://webkul.com/blog/""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_advanced_wishlist&version=12.0",
  "depends"              :  [
                             'website_sale','website_wishlist',
                            ],
  "data"                 :  [
                              'security/ir.model.access.csv',
                              
                              'views/wk_templates.xml',
                              'views/wk_wishlist.xml',
                              'views/res_config_settings_views.xml',
                            ],
  "demo"                 :  ['data/data.xml',],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  110,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
