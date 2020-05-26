# Sale.Order.Line Mods
# Mod by SSI - Chad Thompson
# Mod Date - 1/11/2019
from datetime import timedelta, time
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_view_sales(self):
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365), time.min))
        done_states = self.env['sale.report']._get_done_states()

        action = self.env.ref('sale.action_order_report_all').read()[0]
        action['domain'] = [
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids),
            # ('confirmation_date', '>=', date_from),
        ]
        action['context'] = {
            'group_by': 'confirmation_date:week',
            'pivot_measures': ['product_uom_qty'],
        }
        return action


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_view_sales(self):
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365), time.min))
        done_states = self.env['sale.report']._get_done_states()

        action = self.env.ref('sale.action_order_report_all').read()[0]
        action['domain'] = [
            ('state', 'in', done_states),
            ('product_tmpl_id', 'in', self.ids),
            # ('confirmation_date', '>=', date_from),
        ]
        action['context'] = {
            'group_by': 'confirmation_date:week',
            'pivot_measures': ['product_uom_qty'],
        }
        return action

