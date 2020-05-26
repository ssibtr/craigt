# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import inspect
import logging
import hashlib
import re

from werkzeug import urls
from werkzeug.exceptions import NotFound

from odoo import api, fields, models, tools
from odoo.addons.http_routing.models.ir_http import slugify, _guess_mimetype
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.portal.controllers.portal import pager
from odoo.tools import pycompat
from odoo.http import request
from odoo.osv import expression
from odoo.osv.expression import FALSE_DOMAIN
from odoo.tools.translate import _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

class Website(models.Model):

    _inherit = "website"

    @api.model
    def website_domain_ssi(self, website_id=False):
        return [('show_websites', 'ilike', request.website.name)]
#         return [('website_id', 'in', (False, website_id or self.id))]

class WebsiteMultiMixin(models.AbstractModel):

    _inherit = 'website.multi.mixin'

    @api.multi
    def can_access_from_current_website(self, website_id=False):
        can_access = False
        for record in self:
            for show in record.show_websites:
                if (website_id or show.id) in (False, request.website.id):
                    can_access = True
                    continue
        return can_access

class BlogBlog(models.Model):
    _inherit = 'blog.blog'

    show_websites = fields.Many2many('website', string="Show on Websites")
