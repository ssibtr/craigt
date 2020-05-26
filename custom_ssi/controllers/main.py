from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_sale.controllers import main
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.sale.controllers.product_configurator import ProductConfiguratorController
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.osv import expression
import werkzeug
import json
import logging
from collections import deque
from odoo.tools import ustr
from odoo.tools.misc import xlwt
import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

PPG = 21  # Products Per Page
PPR = 3   # Products Per Row
main.PPG = 21  # Products Per Page
main.PPR = 3   # Products Per Row

class WebsiteSale(WebsiteSale):
   
    @http.route(['/shop/cart/restorecart'],
      type='json',
      auth="public",
      methods=['POST'],
      website=True,
      multilang=False,
      csrf=False)
    def restore_cart_custom(self,  **args):
        request_data = request.httprequest.data
        so_id = json.loads(request_data.decode("utf-8"))['so_id']
        try:
            so = request.env['sale.order'].sudo().search(
                [('id', '=', so_id)], limit=1)
            if so:
                so.sudo().write({'state': 'draft'})
                data = {'message': 'Success', 'state': so.state}
            else:
                data = {'message': 'Failled ELSE'}
        except Exception:
            data = {'message': 'Failled EXCEPT'}
        return data
    
    @http.route(['/shop/cart/po'], 
      type='json', 
      auth="public", 
      methods=['POST'], 
      website=True, 
      multilang=False, 
      csrf=False)
    def add_po_custom(self,  **args):
        input_data = request.httprequest.data
        ref = json.loads(input_data.decode("utf-8"))['ref']
        so = json.loads(input_data.decode("utf-8"))['so']
#        sale_order_id = request.session.get('sale_order_id')
        data = {}
        try:
            sale_order = request.env['sale.order'].sudo().search([('id', '=', so)], limit=1)
            if sale_order:
                sale_order.sudo().write({'client_order_ref': ref})
                data = {'ref': ref, 'SO': so}
            else:
                data = {'message': 'not found', 'ref': ref}
        except Exception:
            pass
        return data

    @http.route(['/shop/cart/savecart'], 
      type='json', 
      auth="public", 
      methods=['POST'], 
      website=True, 
      multilang=False, 
      csrf=False)
    def save_cart_custom(self,  **args):
        sale_order_id = request.session.get('sale_order_id')
        try:
            so = request.env['sale.order'].sudo().search([('id', '=', sale_order_id)], limit=1)
            if so:
                so.sudo().write({'state': 'saved'})
                data = {'message': 'Success', 'state': so.state}
            else:
                data = {'message': 'Failled'}
        except Exception:
            data = {'message': 'Failled'}
        return data


    @http.route(['/web/buyreport'], 
        type='http', 
        methods=['GET'], 
        csrf=False)
    def buyreport(self, **args):
        products = request.env['product.product'].sudo().search(
          ['&', ('sale_ok', '=', True), 
           ('x_status', 'not in', ['G1','G2', 'G3', 'T1', 'T2', 'S1', 'K1'])
          ])
        myHeaders = [
          'EDP No', 
          'Internal Reference', 
          'Name',
          'Vendors/Vendor/Display Name',
          'Status', 
          'Buyer Code', 
          'Min Buy', 
          'Case Qty', 
          'Category', 
          'List Price', 
          'Cost', 
          'Quantity On Hand', 
          'On PO', 
          'Outgoing', 
          'Forecasted Quantity', 
          'Available Inventory', 
          'Backorders Total Count', 
          'Backorders Total Quantity',
#           'W0', 'W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9',
#           'W10', 'W11', 'W12', 'W13', 'W14', 'W15', 'W16', 'W17', 'W18', 'W19',
#           'W20', 'W21', 'W22', 'W23', 'W24', 'W25', 'W26', 'W27', 'W28', 'W29',
#           'W30', 'W31', 'W32', 'W33', 'W34', 'W35', 'W36', 'W37', 'W38', 'W39',
#           'W40', 'W41', 'W42', 'W43', 'W44', 'W45', 'W46', 'W47', 'W48', 'W49',
#           'W50', 'W51', 'W52'
        ]
        
        now = datetime.datetime.now()
        currentWeek = datetime.date(now.year, now.month, now.day).isocalendar()[1]
        date_from = (now-relativedelta(months=12))
        for x in range(0, 53):
            head_date = (date_from+relativedelta(weeks=x)).isocalendar()
            myHeaders.append([("W%i %i" % (head_date[1], head_date[0]))])

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Buy Report')
        row = 0
        col = 0

        for header in myHeaders:
            worksheet.write(col , row, header)
            row = row + 1

        col = 1
        all_sales = ''
        for p in products:
#	         if p.x_status != 'G1' and p.x_status != 'G2' and p.x_status != 'G3' and p.x_status != 'T1' and p.x_status != 'T2' and p.x_status != 'S1' and p.x_status != 'K1':
            if p.x_status:
                row = 0    
  #         	DONT FORGET TO SET THIS BACK TO != FALSE
                backorders = request.env['stock.picking'].sudo().search(
                  [('product_id', '=', p.id), ('backorder_id', '!=', False), ('state', 'in',["confirmed","waiting"])]
                )

                total_qty = 0
                total_count = 0
                orders = []
                for b in backorders:
                    if b.sale_id.name not in orders:
                        orders.append(b.sale_id.name)
                        total_count = total_count + 1
                        for l in b.move_lines:
                            total_qty = total_qty + l.product_uom_qty
          
          
			  # MAKE SURE THAT THE PRODUCT ISNT IN THE SAME ORDER BEFORE COUNTING picking_type_id = 1
			  # DO THE SAME THING AS I AM DOING IN BO QTY
			  # REPLACE OUTGOING WITH ON PO AND PUT THAT NUMBER IN
			  
                on_pos = request.env['stock.move'].sudo().search(
                  [('product_id', '=', p.id), ('location_id', '=', 8), ("state","in",["assigned","confirmed","waiting"])]
                )
#	         	return str(on_pos)
                total_po_qty = 0 
                for o in on_pos:
                    total_po_qty = total_po_qty + o.product_uom_qty

                actual_cost = 0
                roundedCost = 0
                vendor = ''
                for seller in p.seller_ids.filtered(lambda x: x.company_id.id == 1):
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
                        vendor = str(seller.display_name)
                    except IndexError:
                        pass          
                    break          

                forecast = p.qty_available + total_po_qty - p.outgoing_qty

                currentRow = [
                    str(p.x_edpno),  
                    str(p.default_code),  
                    str(p.display_name), 
                    vendor,
                    str(p.x_status), 
                    p.x_buyer, 
                    str(int(min_qty)), 
                    str(int(case_qty)), 
                    p.categ_id.name, 
                    str(int(p.list_price)), 
                    roundedCost, 
                    str(int(p.qty_available)), 
                    str(int(total_po_qty)), 
                    str(int(p.outgoing_qty)), 
                    str(int(forecast)), 
                    str(int(p.qty_available - p.outgoing_qty)),
                    str(total_count), 
                    str(int(total_qty))
                ]

                for currentColumn in currentRow:
                    worksheet.write(col , row, currentColumn)
                    row = row + 1
                
                if p.used_in_bom_count > 0:
                    product_ids = [p.id]
                    multipliers = [1]
                    for b in p.bom_line_ids:
                        newId = products = request.env['product.product'].sudo().search([('product_tmpl_id', '=', b.parent_product_tmpl_id.id)]).id

                        product_ids.append(newId)
                        multipliers.append(b.product_qty)
                        weeksArray = []
                        for i, item in enumerate(product_ids):
                            multiplier = multipliers[i]
                            itemSales = request.env['sale.report'].sudo().read_group(
                              domain=[
                                  ('product_id', '=', item), 
                                  ('state', '=', 'sale'),
                                  ('confirmation_date','>=', date_from.strftime('%Y-%m-%d')),
                                  ('confirmation_date','<=',now.strftime('%Y-%m-%d'))
                              ],
                              fields=['product_uom_qty', 'confirmation_date', 'product_id'], 
                              groupby=['confirmation_date:week']
                            )
                            for s in itemSales:
                                if(s['confirmation_date:week']):
                                    try:
                                        if (str(s['confirmation_date:week'].split(" ",1)[1]) == str(now.year)):
                                            weekIndex = 52 + 18 - (int(currentWeek) - int(s['confirmation_date:week'].split(" ",1)[0][1:3])) 
                                        else:
                                            weekIndex = (int(s['confirmation_date:week'].split(" ",1)[0][1:3]) - int(currentWeek)) + 18
                                    except:
                                        return str(s)
                                    string = str(int(s['product_uom_qty']) * int(multiplier))
                                    try:
                                        appendCount = 0
                                        for w in weeksArray:
                                            if w[0] == weekIndex:
                                                w[1] = weekIndex
#                                                 w[1] = str(int(w[1]) + int(string))
                                                appendCount = appendCount + 1
                                            if appendCount == 0:
#                                                 weeksArray.append([weekIndex, string])
                                                weeksArray.append([weekIndex, weekIndex])
                                    except:
                                        pass

								# fake data by adding a bunch of tupples already to the weeksArray
								# add to those tupples by running that loop above
								# aggregate numbers by first index in tupple


                        for w in weeksArray:
                            try:
                                worksheet.write(col , w[0], w[1])
                            except:
                                pass



					# return str(p.used_in_bom_count)
#                       orderby='confirmation_date:week DESC'
                else:
                    sales = request.env['sale.report'].sudo().read_group(
                      domain=[('product_id', '=', p.id), 
                              ('state', '=', 'sale'),
                              ('confirmation_date','>=', date_from.strftime('%Y-%m-%d')),
                              ('confirmation_date','<=',now.strftime('%Y-%m-%d'))
                             ],
                      fields=['product_uom_qty', 'confirmation_date', 'product_id'], 
                      groupby=['confirmation_date:week']
                    )
                    for s in sales:
                        if(s['confirmation_date:week']):
                            try:
                                if (str(s['confirmation_date:week'].split(" ",1)[1]) == str(now.year)):
                                    weekIndex = 52 + 18 - (int(currentWeek) - int(s['confirmation_date:week'].split(" ",1)[0][1:3])) 
                                else:
                                    weekIndex = (int(s['confirmation_date:week'].split(" ",1)[0][1:3]) - int(currentWeek)) + 18
                            except:
                                return str(s)
                            string = str(int(s['product_uom_qty']))
						#             string = str(s['confirmation_date:week']).split(" ",1)[0][1:3] + ' => ' + str(weekIndex)

                            try:
                                worksheet.write(col , weekIndex, string)
                            except:
                                pass

                col = col + 1

        response = request.make_response(None, headers=[('Content-Type', 'application/vnd.ms-excel'), ('Content-Disposition', 'attachment; filename=buyreport-'+str(datetime.datetime.now())+'.xls')], cookies={'fileToken': 'token'})
        workbook.save(response.stream)

        return response


    
    @http.route(['/shop/cart/custom_cart'], type='http', auth="public", methods=['POST'], website=True, multilang=False)
    def cart_update_custom(self, product_iref_1, add_qty_1, product_iref_2, add_qty_2, product_iref_3, add_qty_3, product_iref_4, add_qty_4, product_iref_5, add_qty_5, product_iref_6, add_qty_6, product_iref_7, add_qty_7,  product_iref_8, add_qty_8, product_iref_9, add_qty_9, product_iref_10, add_qty_10, set_qty=0, goto_shop=None, lang=None, **kw):
        if lang:
            request.website = request.website.with_context(lang=lang)
        order = request.website.sale_get_order(force_create=1)
        try:
            product = request.env['product.product'].sudo().search([('default_code', '=', product_iref_1.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_1 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_1),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_2.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_2 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_2),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass
        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_3.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_3 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_3),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_4.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_4 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_4),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_5.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_5 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_5),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_6.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_6 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_6),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_7.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_7 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_7),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_8.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_8 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_8),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_9.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_9 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_9),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass

        try:
            product = request.env['product.product'].search([('default_code', '=', product_iref_10.upper())], limit=1)
            if product:
                optional_product_ids = []
                if hasattr(product, 'optional_product_ids'):
                    option_ids = product.optional_product_ids.mapped('product_variant_ids').ids
                    for k, v in kw.items():
                        if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                            optional_product_ids.append(int(v))

                # attributes = self._filter_attributes(**kw)

                value = {}
                if add_qty_10 or set_qty:
                    value = order._cart_update(
                        product_id=int(product.id),
                        add_qty=int(add_qty_10),
                        set_qty=int(set_qty),
                        # attributes=attributes,
                        # optional_product_ids=optional_product_ids
                    )

                # options have all time the same quantity
                for option_id in optional_product_ids:
                    order._cart_update(
                        product_id=option_id,
                        set_qty=value.get('quantity'),
                        attributes=attributes,
                        linked_line_id=value.get('line_id')
                    )
        except Exception:
            pass
        # data = {'message': 'not found'}
        # return data
        return werkzeug.utils.redirect('/shop/cart', 301)

    @http.route(['/shop/cart/check_for_item'], type='json', auth="public", methods=['POST'], website=True, multilang=False, csrf=False)
    def check_for_item(self,  **args):
        input_data = request.httprequest.data
        ref = json.loads(input_data.decode("utf-8"))['ref']
        data = {'message': 'Fail'}
        try:
            product = request.env['product.product'].sudo().search([('sale_ok', '=', True), ('default_code', '=', ref.upper())], limit=1)
            if product:
                data = {'message': 'found', 'ref': ref.upper(), 'product': product.name}
            else:
                data = {'message': 'not found', 'ref': ref.upper()}
        except Exception:
            pass
        return data
				

    @http.route(['/shop/printQuote'], type='http', auth="public", website=True)
    def print_salequote(self, **kwargs):
#         sale_order_id = request.session.get('sale_order_id')
        carrier_id=0
        order = request.website.sale_get_order()
        if order.carrier_id:
            carrier_id = int(carrier_id)
        else:
            carrier_id = 29
        if order:
            order._check_carrier_quotation(force_carrier_id=carrier_id)
        
        if order.id:
            pdf, _ = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([order.id])
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return request.redirect('/shop')
            
    def _get_search_domain(self, search, category, attrib_values):
#         domain = request.website.sale_product_domain()
        domain = [('show_websites', 'ilike', request.website.name)]

        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch), ('x_sa_item', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category", "[('show_websites', 'ilike', request.website.name)]"):category>''',
        '''/shop/category/<model("product.public.category", "[('show_websites', 'ilike', request.website.name)]"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        if category:
            category = request.env['product.public.category'].search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)

        Category = request.env['product.public.category']
        search_categories = False
        search_product = Product.search(domain)
        if search:
            categories = search_product.mapped('public_categ_ids')
            search_categories = Category.search([('id', 'parent_of', categories.ids)] + request.website.website_domain_ssi())
            categs = search_categories.filtered(lambda c: not c.parent_id)
        else:
            categs = Category.search([('parent_id', '=', False)] + request.website.website_domain_ssi())

        parent_category_ids = []
        if category:
            url = "/shop/category/%s" % slug(category)
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('attribute_line_ids.value_ids', '!=', False), ('attribute_line_ids.product_tmpl_id', 'in', search_product.ids)])        
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        compute_currency = self._get_compute_currency(pricelist, products[:1])

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'parent_category_ids': parent_category_ids,
            'search_categories_ids': search_categories and search_categories.ids,
        }
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)

   
