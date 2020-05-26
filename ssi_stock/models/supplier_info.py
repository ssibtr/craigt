# -*- coding: utf-8 -*-
from odoo import fields,models,api, _

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    case_qty = fields.Float('Case Qty')
