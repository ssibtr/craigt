# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

    
class BackStockReport(models.Model):
    _name = "back.stock.report"
    _description = "Back Stock Report"
    _auto = False
    _order = 'product_name'

    product_name = fields.Char('Product Name', readonly=True)
    primary_location = fields.Many2one('stock.location', 'Primary Location', readonly=True)
    secondary_location = fields.Many2one('stock.location', 'Secondary Location', readonly=True)
    product_id = fields.Many2one('product.product', 'Product ID', readonly=True)
    status = fields.Char('Status', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    qty_oh = fields.Float('Qty On Hand', readonly=True)
    qty_ord = fields.Float('Qty to Deliver', readonly=True)
    qty_prm = fields.Float('Qty Primary', readonly=True)
    qty_sec = fields.Float('Qty Secondary', readonly=True)
    qty_rsv = fields.Float('Qty Reserved', readonly=True)
    qty_po = fields.Float('Qty On PO', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        # with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            SELECT
                MIN(q.id) as id,
                pt.name as product_name,
                pt.x_primary_location as primary_location,
                l.id as secondary_location,
                pp.id as product_id,
                pt.x_status as status,
                pt.uom_id as product_uom,
                (SELECT Sum(remaining_qty) FROM stock_move sm WHERE sm.product_id = pp.id) as qty_oh,
                (SELECT Sum(product_uom_qty) FROM stock_move smo 
                    WHERE smo.product_id = pp.id and state in ('assigned','confirmed','waiting') 
                        AND smo.picking_type_id in (115,116,117))
                as qty_ord,
                (SELECT Sum(product_uom_qty) FROM stock_move 
                    WHERE product_id = pp.id and state in ('assigned','confirmed','waiting') 
                        AND picking_type_id in (1))
                as qty_po,
                SUM(q.reserved_quantity) as qty_rsv,
                SUM(pq.quantity) as qty_prm,
                SUM(q.quantity) as qty_sec
            FROM
                stock_quant q
                LEFT JOIN stock_location l ON q.location_id = l.id
                LEFT JOIN product_product pp ON q.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN stock_quant pq ON pq.product_id = pp.id AND pq.location_id = pt.x_primary_location
            WHERE
                l.complete_name LIKE '%WH/%' and pp.active
            GROUP BY
                product_name, pp.id, status, product_uom, primary_location, secondary_location
        """
#          UNION
#             SELECT
#                 MIN(q.id) as id,
#                 p.name as product_name,
#                 p.x_primary_location as primary_location,
#                 l.name as secondary_location,
#                 p.id as product_id,
#                 p.uom_id as product_uom,
#                 SUM(q.quantity) as qty_oh,
#                 SUM(q.reserved_quantity) as qty_rsv
#             FROM
#                 stock_quant q
#                 LEFT JOIN stock_location l ON q.location_id = l.id
#                 LEFT JOIN product_template p ON q.product_id = p.id
#             WHERE
#                 q.location_id = p.x_primary_location AND
#                 q.quantity <= 0
#             GROUP BY
#                 product_name, p.id, product_uom, primary_location, secondary_location

        return select_

    @api.model_cr
    def init(self):
        self._table = 'back_stock_report'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    @api.multi
    def payroll_export(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/csv/download/payroll/%s/attendance/%s'%(self.week_no, self.id),
            'target': 'blank',
        }

    @api.model
    def _csv_download(self,vals):
        # week = vals.get('week')
        # attendance_id = vals.get('attendance_id')

        # attendance = self.env['hr.attendance.report'].search([('week_no','=',week)])

        # columns = ['Employee ID', 'Code', 'Type', 'Hours']
        # csv = ','.join(columns)
        # csv += "\n"

        # if len(attendance) > 0:
            # for att in attendance:
                # emp_id = att.employee_badge if att.employee_badge else ''
                # hours = att.hours if att.hours else 0
                # overtime = att.over_time if att.over_time else 0
                # overtime_group = 'OT' if 'Regular' in att.overtime_group else att.overtime_group

                # Regular Time
                # data = [
                    # emp_id,
                    # 'E',
                    # 'REG',
                    # str(hours),
                # ]
                # csv_row = u'","'.join(data)
                # csv += u"\"{}\"\n".format(csv_row)

                # Over Time
                # if att.over_time:
                    # data = [
                        # emp_id,
                        # 'E',
                        # overtime_group,
                        # str(overtime),
                    # ]
                    # csv_row = u'","'.join(data)
                    # csv += u"\"{}\"\n".format(csv_row)

        return csv

