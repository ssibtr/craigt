# -*- coding: utf-8 -*-
from odoo import fields,models,api
from odoo.addons import decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    show_websites = fields.Many2many('website', string="Show on Websites")
    sort_price = fields.Float(string="Sort Price", compute='_compute_sort_price', digits=dp.get_precision('.2f%'), store=True)
    sa_sort_price = fields.Float(string="SA Sort Price", compute='_compute_sa_sort_price', digits=dp.get_precision('.2f%'), store=True)

    @api.multi
    @api.depends('list_price', 'item_ids')
    def _compute_sort_price(self):
        for template in self:
            template.sort_price = template.list_price 
            web_prc = template.item_ids.filtered(lambda c: c.pricelist_id.id == 92)
            if web_prc:
                if web_prc[0].fixed_price > 0:
                    template.sort_price = web_prc[0].fixed_price
    
    @api.multi
    @api.depends('list_price', 'item_ids')
    def _compute_sa_sort_price(self):
        for template in self:
            template.sa_sort_price = template.list_price
            web_prc = template.item_ids.filtered(lambda c: c.pricelist_id.id == 124)
            if web_prc:
                if web_prc[0].fixed_price > 0:
                    template.sa_sort_price = web_prc[0].fixed_price
    

class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    show_websites = fields.Many2many('website', string="Show on Websites")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _anglo_saxon_sale_move_lines(self, name, product, uom, qty, price_unit, currency=False, amount_currency=False, fiscal_position=False, account_analytic=False, analytic_tags=False):
        """Prepare dicts describing new journal COGS journal items for a product sale.

        Returns a dict that should be passed to `_convert_prepared_anglosaxon_line()` to
        obtain the creation value for the new journal items.

        :param Model product: a product.product record of the product being sold
        :param Model uom: a product.uom record of the UoM of the sale line
        :param Integer qty: quantity of the product being sold
        :param Integer price_unit: unit price of the product being sold
        :param Model currency: a res.currency record from the order of the product being sold
        :param Interger amount_currency: unit price in the currency from the order of the product being sold
        :param Model fiscal_position: a account.fiscal.position record from the order of the product being sold
        :param Model account_analytic: a account.account.analytic record from the line of the product being sold
        """

#         raise UserError(_(self.env.context))
        force_company = self.env.context.get('force_company')
#         raise UserError(_(force_company))
        if product.type == 'product' and product.valuation == 'real_time' and force_company != 6:
            accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            # debit account dacc will be the output account
            dacc = accounts['stock_output'].id
            # credit account cacc will be the expense account
            cacc = accounts['expense'].id
            if dacc and cacc:
                return [
                    {
                        'type': 'src',
                        'name': name[:64],
                        'price_unit': price_unit,
                        'quantity': qty,
                        'price': price_unit * qty,
                        'currency_id': currency and currency.id,
                        'amount_currency': amount_currency,
                        'account_id': dacc,
                        'product_id': product.id,
                        'uom_id': uom.id,
                        'account_analytic_id': account_analytic and account_analytic.id,
                        'analytic_tag_ids': analytic_tags and analytic_tags.ids and [(6, 0, analytic_tags.ids)] or False,
                    },

                    {
                        'type': 'src',
                        'name': name[:64],
                        'price_unit': price_unit,
                        'quantity': qty,
                        'price': -1 * price_unit * qty,
                        'currency_id': currency and currency.id,
                        'amount_currency': -1 * amount_currency,
                        'account_id': cacc,
                        'product_id': product.id,
                        'uom_id': uom.id,
                        'account_analytic_id': account_analytic and account_analytic.id,
                        'analytic_tag_ids': analytic_tags and analytic_tags.ids and [(6, 0, analytic_tags.ids)] or False,
                    },
                ]
        return []

