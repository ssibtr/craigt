# Sale.Order.Line Mods
# Mod by SSI - Chad Thompson
# Mod Date - 1/11/2019
import datetime
from dateutil.relativedelta import relativedelta

from odoo import tools
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    client_order_ref =  fields.Char(string='Customer PO');

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('saved', 'Saved'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    carrier_id = fields.Many2one(track_visibility='onchange')
		
    @api.onchange('client_order_ref')
    def _check_duplicates(self):
        duplicates = self.env['sale.order'].search([
            ('client_order_ref','=', self.client_order_ref),
            ('name', '!=', self.name)
        ])
        # ('partner_id.name','=', self.partner_id.name),    // took out partner check on PO

				# if isinstance(duplicates, list):
        for d in duplicates:
          if str(d.id) != 'False' and self.client_order_ref:
            return {
                'warning': {'title': "Warning", 'message': "This Purchase Order reference already exists for this customer. Sale Order ->  " + str(d.name)},
            }
        
    @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        # Ignore the status of the deposit product
        deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
        line_invoice_status_all = [(d['order_id'][0], d['invoice_status']) for d in self.env['sale.order.line'].read_group([('order_id', 'in', self.ids), ('product_id', '!=', deposit_product_id.id)], ['order_id', 'invoice_status'], ['order_id', 'invoice_status'], lazy=False)]
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([('origin', 'like', order.name), ('company_id', '=', order.company_id.id), ('type', 'in', ('out_invoice', 'out_refund'))])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])

            # Search for refunds as well
            domain_inv = expression.OR([
                ['&', ('origin', '=', inv.number), ('journal_id', '=', inv.journal_id.id)]
                for inv in invoice_ids if inv.number
            ])
            if domain_inv:
                refund_ids = self.env['account.invoice'].search(expression.AND([
                    ['&', ('type', '=', 'out_refund'), ('origin', '!=', False)], 
                    domain_inv
                ]))
            else:
                refund_ids = self.env['account.invoice'].browse()

            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]

            if order.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'

            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

#     line_margin = fields.Float(compute='_compute_margin', digits=dp.get_precision('.2f%'), store=True)
#     product_status = fields.Char(string="Product Status", compute='_compute_initial', store=True)
    product_status = fields.Char(string="Product Status", compute='_compute_product_status')

    def _compute_product_status(self):
        # When updating product, save the status.
        for record in self:
            record.product_status = record.product_id.x_status

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # When updating product, save the status.
         self.product_status = self.product_id.x_status

#     def _compute_initial(self):
#         for record in self:
#             record.product_status = record.x_studio_status

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


class SaleReport(models.Model):
    _inherit = "sale.report"
    
    customer_email = fields.Char('Customer Email', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['customer_email'] = ', partner.email as customer_email'

        groupby += ', partner.email'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        

class SaleBuyReport(models.Model):
    _name = "sale.buy.report"
    _description = "Sales Buy Report Data"
    _order = 'product_id desc'

    product_id = fields.Many2one('product.product', 'Product Variant')
    prod_template_id = fields.Many2one('product.template', 'Product Template')
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    min_qty = fields.Float('Min Qty')
    case_qty = fields.Float('Case Qty')
    cost = fields.Float('Cost')
    total_po_qty = fields.Float('Total PO Qty')
    forecast_qty = fields.Float('Forecast Qty')
    available_qty = fields.Float('Available Qty')
    bo_count = fields.Integer('BO Count')
    bo_qty = fields.Float('BO Qty')
    qty_w0 = fields.Float('W0 Qty')
    qty_w1 = fields.Float('W1 Qty')
    qty_w2 = fields.Float('W2 Qty')
    qty_w3 = fields.Float('W3 Qty')
    qty_w4 = fields.Float('W4 Qty')
    qty_w5 = fields.Float('W5 Qty')
    qty_w6 = fields.Float('W6 Qty')
    qty_w7 = fields.Float('W7 Qty')
    qty_w8 = fields.Float('W8 Qty')
    qty_w9 = fields.Float('W9 Qty')
    qty_w10 = fields.Float('W10 Qty')
    qty_w11 = fields.Float('W11 Qty')
    qty_w12 = fields.Float('W12 Qty')
    qty_w13 = fields.Float('W13 Qty')
    qty_w14 = fields.Float('W14 Qty')
    qty_w15 = fields.Float('W15 Qty')
    qty_w16 = fields.Float('W16 Qty')
    qty_w17 = fields.Float('W17 Qty')
    qty_w18 = fields.Float('W18 Qty')
    qty_w19 = fields.Float('W19 Qty')
    qty_w20 = fields.Float('W20 Qty')
    qty_w21 = fields.Float('W21 Qty')
    qty_w22 = fields.Float('W22 Qty')
    qty_w23 = fields.Float('W23 Qty')
    qty_w24 = fields.Float('W24 Qty')
    qty_w25 = fields.Float('W25 Qty')
    qty_w26 = fields.Float('W26 Qty')
    qty_w27 = fields.Float('W27 Qty')
    qty_w28 = fields.Float('W28 Qty')
    qty_w29 = fields.Float('W29 Qty')
    qty_w30 = fields.Float('W30 Qty')
    qty_w31 = fields.Float('W31 Qty')
    qty_w32 = fields.Float('W32 Qty')
    qty_w33 = fields.Float('W33 Qty')
    qty_w34 = fields.Float('W34 Qty')
    qty_w35 = fields.Float('W35 Qty')
    qty_w36 = fields.Float('W36 Qty')
    qty_w37 = fields.Float('W37 Qty')
    qty_w38 = fields.Float('W38 Qty')
    qty_w39 = fields.Float('W39 Qty')
    qty_w40 = fields.Float('W40 Qty')
    qty_w41 = fields.Float('W41 Qty')
    qty_w42 = fields.Float('W42 Qty')
    qty_w43 = fields.Float('W43 Qty')
    qty_w44 = fields.Float('W44 Qty')
    qty_w45 = fields.Float('W45 Qty')
    qty_w46 = fields.Float('W46 Qty')
    qty_w47 = fields.Float('W47 Qty')
    qty_w48 = fields.Float('W48 Qty')
    qty_w49 = fields.Float('W49 Qty')
    qty_w50 = fields.Float('W50 Qty')
    qty_w51 = fields.Float('W51 Qty')
    qty_w52 = fields.Float('W52 Qty')

    @api.multi
    def _get_buy_data(self):
        # Clear all records
        self.search([('id', '!=', False)]).unlink()
        
        now = datetime.datetime.now()
        currentWeek = datetime.date(now.year, now.month, now.day).isocalendar()[1]
        date_from = (now-relativedelta(months=12))
        start_date = date_from.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        row = 0
        col = 0
        ct = 0
        all_sales = ''        

        _query = """
            SELECT
                p.id as prod_id,
                t.x_status as x_status,
                p.product_tmpl_id as prod_template_id,
                sales.*
            FROM product_product p
                left join product_template t on (p.product_tmpl_id=t.id)
                left join (SELECT
                            l.product_id,
                            extract(year from s.confirmation_date) as year,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '01' THEN l.product_uom_qty ELSE 0 END) as w1,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '02' THEN l.product_uom_qty ELSE 0 END) as w2,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '03' THEN l.product_uom_qty ELSE 0 END) as w3,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '04' THEN l.product_uom_qty ELSE 0 END) as w4,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '05' THEN l.product_uom_qty ELSE 0 END) as w5,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '06' THEN l.product_uom_qty ELSE 0 END) as w6,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '07' THEN l.product_uom_qty ELSE 0 END) as w7,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '08' THEN l.product_uom_qty ELSE 0 END) as w8,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '09' THEN l.product_uom_qty ELSE 0 END) as w9,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '10' THEN l.product_uom_qty ELSE 0 END) as w10,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '11' THEN l.product_uom_qty ELSE 0 END) as w11,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '12' THEN l.product_uom_qty ELSE 0 END) as w12,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '13' THEN l.product_uom_qty ELSE 0 END) as w13,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '14' THEN l.product_uom_qty ELSE 0 END) as w14,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '15' THEN l.product_uom_qty ELSE 0 END) as w15,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '16' THEN l.product_uom_qty ELSE 0 END) as w16,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '17' THEN l.product_uom_qty ELSE 0 END) as w17,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '18' THEN l.product_uom_qty ELSE 0 END) as w18,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '19' THEN l.product_uom_qty ELSE 0 END) as w19,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '20' THEN l.product_uom_qty ELSE 0 END) as w20,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '21' THEN l.product_uom_qty ELSE 0 END) as w21,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '22' THEN l.product_uom_qty ELSE 0 END) as w22,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '23' THEN l.product_uom_qty ELSE 0 END) as w23,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '24' THEN l.product_uom_qty ELSE 0 END) as w24,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '25' THEN l.product_uom_qty ELSE 0 END) as w25,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '26' THEN l.product_uom_qty ELSE 0 END) as w26,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '27' THEN l.product_uom_qty ELSE 0 END) as w27,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '28' THEN l.product_uom_qty ELSE 0 END) as w28,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '29' THEN l.product_uom_qty ELSE 0 END) as w29,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '30' THEN l.product_uom_qty ELSE 0 END) as w30,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '31' THEN l.product_uom_qty ELSE 0 END) as w31,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '32' THEN l.product_uom_qty ELSE 0 END) as w32,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '33' THEN l.product_uom_qty ELSE 0 END) as w33,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '34' THEN l.product_uom_qty ELSE 0 END) as w34,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '35' THEN l.product_uom_qty ELSE 0 END) as w35,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '36' THEN l.product_uom_qty ELSE 0 END) as w36,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '37' THEN l.product_uom_qty ELSE 0 END) as w37,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '38' THEN l.product_uom_qty ELSE 0 END) as w38,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '39' THEN l.product_uom_qty ELSE 0 END) as w39,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '40' THEN l.product_uom_qty ELSE 0 END) as w40,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '41' THEN l.product_uom_qty ELSE 0 END) as w41,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '42' THEN l.product_uom_qty ELSE 0 END) as w42,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '43' THEN l.product_uom_qty ELSE 0 END) as w43,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '44' THEN l.product_uom_qty ELSE 0 END) as w44,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '45' THEN l.product_uom_qty ELSE 0 END) as w45,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '46' THEN l.product_uom_qty ELSE 0 END) as w46,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '47' THEN l.product_uom_qty ELSE 0 END) as w47,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '48' THEN l.product_uom_qty ELSE 0 END) as w48,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '49' THEN l.product_uom_qty ELSE 0 END) as w49,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '50' THEN l.product_uom_qty ELSE 0 END) as w50,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '51' THEN l.product_uom_qty ELSE 0 END) as w51,
                            sum(CASE WHEN to_char(date_trunc('week', s.confirmation_date), 'WW') = '52' THEN l.product_uom_qty ELSE 0 END) as w52,
                            sum(l.product_uom_qty) as w53
                           FROM
                            sale_order_line l
                            left join sale_order s on (l.order_id=s.id)
                           WHERE
                            s.state = 'sale' AND s.confirmation_date > %s AND s.confirmation_date <= %s AND s.company_id = %s
                           GROUP BY l.product_id, year) as sales on sales.product_id = p.id
            WHERE t.sale_ok = 'True' and t.active = 'True'
                AND t.x_status not in ('G1','G2', 'G3', 'T1', 'T2', 'S1', 'K1')
            ORDER BY p.id
        """
#   AND p.id = 3875  AND s.name = 'SO54176'
        self.env.cr.execute(_query, (start_date, end_date, self.env.user.company_id.id))
        for val in self.env.cr.dictfetchall():
#             raise UserError(_(val))

            if val['prod_id']:
                row = 0    

                w_qty = []
                for i in range(0, 52 - date_from.isocalendar()[1] + 2):
                    if val['year'] == date_from.year:
                        qty = val['w' + str(i + date_from.isocalendar()[1] - 1)]
                    else:
                        qty = 0
                    w_qty.append(qty)
                last_week = {str(val['prod_id']): qty}  
                for j in range(0, now.isocalendar()[1] + 1):
                    if val['year'] == now.year:
                        if j == 0:
                            qty = val['w1'] + last_week[str(val['prod_id'])]
                        else:
                            qty = val['w' + str(j+1)]
                    else:
                        qty = 0
                    w_qty.append(qty)
                        
                exists = self.env['sale.buy.report'].search([('product_id', '=', val['prod_id'])])
                if exists:
                    for i in range(0, 53):
                        if w_qty[i] > 0:
                            br_vals['qty_w'+str(i)] = w_qty[i]
                    exists.write(br_vals)
                else:
                    
      #         	DONT FORGET TO SET THIS BACK TO != FALSE
                    backorders = self.env['stock.picking'].sudo().search(
                      [('product_id', '=', val['prod_id']), 
                       ('backorder_id', '!=', False), 
                       ('company_id', '=', self.env.user.company_id.id),
                       ('state', 'in',["confirmed","waiting"])]
                    )

                    total_bo_qty = 0
                    total_bo_count = 0
                    orders = []
                    br_vals = {}
                    for b in backorders:
                        if b.sale_id.name not in orders:
                            orders.append(b.sale_id.name)
                            total_bo_count = total_bo_count + 1
                            for l in b.move_lines:
                                total_bo_qty = total_bo_qty + l.product_uom_qty

                  # MAKE SURE THAT THE PRODUCT ISNT IN THE SAME ORDER BEFORE COUNTING picking_type_id = 1
                  # DO THE SAME THING AS I AM DOING IN BO QTY
                  # REPLACE OUTGOING WITH ON PO AND PUT THAT NUMBER IN

                    on_pos = self.env['stock.move'].sudo().search(
                      [('product_id', '=', val['prod_id']), 
                       ('location_id', '=', 8),
                       ('company_id', '=', self.env.user.company_id.id),
                       ("state","in",["assigned","confirmed","waiting"])]
                    )
                    total_po_qty = 0
                    for o in on_pos:
                        total_po_qty = total_po_qty + o.product_uom_qty

                    actual_cost = 0
                    roundedCost = 0
                    vendor = False

                    p = self.env['product.product'].search([('id','=',val['prod_id']),('company_id', '=', self.env.user.company_id.id),])
                    for seller in p.product_tmpl_id.seller_ids.filtered(lambda x: x.company_id.id == 1):
                        try :
                            actual_cost = seller.price
                        except:
                            actual_cost = p.standard_price
                        case_qty = seller.case_qty
                        min_qty = seller.min_qty

                        roundedCost = str(round(actual_cost, 2))
                        if(len(roundedCost.split(".",1)[1]) < 2):
                            roundedCost = roundedCost + '0'
                        try:
                            vendor = seller.name.id
                        except IndexError:
                            pass          
                        break          

                    forecast = 0
#                     forecast = p.qty_available + total_po_qty - p.outgoing_qty
                    
                    # Create record with values
                    br_vals = {
                        'product_id': val['prod_id'],
                        'prod_template_id': val['prod_template_id'],
                        'vendor_id': vendor,
                        'min_qty': min_qty,
                        'case_qty': case_qty,
                        'cost': roundedCost,
                        'total_po_qty': total_po_qty,
                        'forecast_qty': forecast,
                        'available_qty': p.qty_available - p.outgoing_qty,
                        'bo_count': total_bo_count,
                        'bo_qty': total_bo_qty,
                    }
                    for i in range(0, 52):
                        if w_qty[i] > 0:
                            br_vals['qty_w'+str(i)] = w_qty[i]
                    self.env['sale.buy.report'].create(br_vals)


