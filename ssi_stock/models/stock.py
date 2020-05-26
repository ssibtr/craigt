# -*- coding: utf-8 -*-
from odoo import fields,models,api, _
from odoo.osv import expression

class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    to_refund = fields.Boolean(string="To Refund (update SO/PO)", default=True, 
                               help='Trigger a decrease of the delivered/received quantity in the associated Sale Order/Purchase Order')

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    def _cron_check_avail(self):
        pickings = self.env['stock.picking'].search([('state', 'in', ('waiting','confirmed'))])
        for pick in pickings:
          pick.action_assign()        
    
    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        for rec in self:
            if rec.sale_id.client_order_ref and rec.sale_id.client_order_ref not in rec.origin:
                org = rec.origin + ' (' + rec.sale_id.client_order_ref + ')'
                rec.write({'origin': org})    
        return res
    

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _search_rule(self, route_ids, product_id, warehouse_id, domain):
        """ First find a rule among the ones defined on the procurement
        group, then try on the routes defined for the product, finally fallback
        on the default behavior
        """
        if warehouse_id:
            domain = expression.AND([['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
        Rule = self.env['stock.rule']
        res = self.env['stock.rule']
        if route_ids:
            res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
            if product_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids),('company_id', '=', warehouse_id.id)], domain]), order='route_sequence, sequence', limit=1)
        if not res and warehouse_id:
            warehouse_routes = warehouse_id.route_ids
            if warehouse_routes:
                res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
        return res