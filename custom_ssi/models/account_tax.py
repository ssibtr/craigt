# Sale.Order.Line Mods
# Mod by SSI - Chad Thompson
# Mod Date - 1/11/2019
from odoo import api, fields, models, _
from odoo.exceptions import UserError


# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'

#     line_margin = fields.Float(compute='_compute_margin', digits=dp.get_precision('.2f%'), store=True)

#     def _compute_margin(self, order_id, product_id, product_uom_id):
#         frm_cur = self.env.user.company_id.currency_id
#         to_cur = order_id.pricelist_id.currency_id
#         purchase_price = product_id.standard_price
#         if product_uom_id != product_id.uom_id:
#             purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
#         ctx = self.env.context.copy()
#         ctx['date'] = order_id.date_order
#         price = frm_cur.with_context(ctx).compute(purchase_price, to_cur, round=False)
#         return price
    
class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def create(self, vals):
        if vals.get('company_id') == 6:
            vals['account_id'] = 446
            vals['refund_account_id'] = 446
        else:
            vals['account_id'] = 219
            vals['refund_account_id'] = 219
        res = super(AccountTax, self).create(vals)
        return res
