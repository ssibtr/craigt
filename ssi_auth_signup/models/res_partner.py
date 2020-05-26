# -*- coding: utf-8 -*-
from odoo import fields,models,api


class Partner(models.Model):
    _inherit = 'res.partner'

    street = fields.Char(track_visibility='onchange')