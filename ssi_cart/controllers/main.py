# -*- coding: utf-8 -*-
# Copyright 2019 Openworx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import datetime

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json
import uuid


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):

        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        SaleOrder = request.env['sale.order']
        partner = request.env.user.partner_id
   

        # BASICALLY
        # IF TEACHER OR SCHOOL DO THIS QUOTE count
        # IF TEACHER BY partner
        # IF SCHOOL BY commercial_partner_id
        # NOW IF TEACHER ONLY SHOW saved AND approval
        # IF SCHOOL Quotation NEEDS TO BE CALLED Approval Pending
        # ELSE DONT CHANGE A THING

        # SENT == APPROVAL Pending
        # DONE == APPROVED

        try:
            if partner.x_studio_approval_role == 'teacher':
                quotation_count = SaleOrder.sudo().search_count([
                    ('partner_id', '=', [
                        partner.id]),
                    ('state', 'in', ['sent', 'cancel', 'done', 'sale'])
                ])
                values['approval_count'] = quotation_count
            if partner.x_studio_approval_role == 'admin':
                pending_count = SaleOrder.sudo().search_count([
                  ('partner_id.parent_id', '=', partner.commercial_partner_id.id),
                  ('state', 'in', ['sent'])
                ])
                approved_count = SaleOrder.sudo().search_count([
                    ('message_partner_ids', 'child_of', [
                        partner.commercial_partner_id.id]),
                    ('state', 'in', ['cancel', 'done', 'sale'])
                ])
                values['pending_count'] = pending_count
                values['approved_count'] = approved_count
        except:
            pass

        cart_count = SaleOrder.sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['saved'])
        ])

        values['cart_count'] = cart_count
        values['approval_role'] = partner.x_studio_approval_role
        # values['contract_count'] = contract_count
        return values

    @http.route(['/my/saved', '/my/saved/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_home_saved(self, page=1):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['saved'])
        ]

        # count for pager
        quotation_count = SaleOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/saved",
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.sudo().search(
            domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'quotation_count': quotation_count,
            'cart_count': quotations,
            'page_name': 'saved',
            'pager': pager,
            'default_url': '/my/saved',
        })

        return request.render("ssi_cart.saved", values)

    @http.route(['/my/pending', '/my/pending/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_home_pewnding(self, page=1):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        domain = [
            ('partner_id.parent_id', '=', partner.commercial_partner_id.id),
            ('state', 'in', ['sent'])
        ]

        pname = ''
        try:
          if partner.commercial_partner_id:
            pname = partner.commercial_partner_id.name
        except:
          pass
        # count for pager
        quotation_count = SaleOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/pending",
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.sudo().search(
            domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'quotation_count': quotation_count,
            'cart_count': quotations,
            'page_name': 'pending',
            'pager': pager,
            'pname': pname,
            'default_url': '/my/pending',
        })

        return request.render("ssi_cart.pending", values)

    @http.route(['/my/approved', '/my/approved/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_home_approved(self, page=1):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        domain = [
                    ('message_partner_ids', 'child_of', [
                        partner.commercial_partner_id.id]),
                    ('state', 'in', ['cancel', 'done', 'sale'])
        ]
        pname = ''
        try:
          pname = partner.commercial_partner_id.name
        except:
          pass

        # count for pager
        quotation_count = SaleOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/approved",
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.sudo().search(
            domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'quotation_count': quotation_count,
            'cart_count': quotations,
            'page_name': 'tapproved',
            'pager': pager,
            'pname': pname,
            'default_url': '/my/approved',
        })

        return request.render("ssi_cart.tapproved", values)

    @http.route(['/my/approval', '/my/approval/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_home_approval(self, page=1):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        domain = [
            ('partner_id', '=', [
             partner.id]),
            ('state', 'in', ['sent', 'cancel'])
        ]
        try:
            if partner.x_studio_approval_role == 'admin':
                domain = [
                    ('message_partner_ids', 'child_of', [
                        partner.commercial_partner_id.id]),
                    ('state', 'in', ['sent', 'cancel', 'done'])
                ]

            if partner.x_studio_approval_role == 'teacher':
                domain = [
                    ('partner_id', '=', [
                        partner.id]),
                    ('state', 'in', ['sent', 'cancel', 'sale', 'done'])
                ]
        except:
            pass

        # count for pager
        quotation_count = SaleOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/approval",
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.sudo().search(
            domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'quotation_count': quotation_count,
            'cart_count': quotations,
            'page_name': 'approval',
            'pager': pager,
            'default_url': '/my/approval',
        })

        return request.render("ssi_cart.approved", values)

    @http.route(['/my/saved/<int:saved>'], type='http', auth="user", website=True)
    def portal_saved_page(self, **kwargs):
        order_id = 0
        report_type = None
        access_token = None
        message = False
        download = False,
        order_id = dict(kwargs)['saved']
        access_token = dict(kwargs)['access_token']

        # so = request.env['sale.order'].sudo().search([('id', '=', order_id)])
        # # return str(so.access_token)
        # access_token = so.access_token
        try:
            order_sudo = self._document_check_access(
                'sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get('view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer')
            _message_post_helper(res_model='sale.order', res_id=order_sudo.id, message=body, token=order_sudo.access_token,
                                 message_type='notification', subtype="mail.mt_note", partner_ids=order_sudo.user_id.sudo().partner_id.ids)

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('website_published', '=', True),
                 ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('specific_countries', '=', False), ('country_ids',
                                                           'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                                                     (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search(
                [('partner_id', '=', order_sudo.partner_id.id),
                 ('acquirer_id', 'in', acquirers.filtered(lambda acq: acq.payment_flow == 's2s').ids)])

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render('ssi_cart.saved_page', values)

    @http.route(['/my/approval/<int:approved>'], type='http', auth="user", website=True)
    def portal_approved_page(self, **kwargs):
        order_id = 0
        report_type = None
        access_token = None
        message = False
        download = False,
        isTeacher = False,
        order_id = dict(kwargs)['approved']
        access_token = dict(kwargs)['access_token']

        # so = request.env['sale.order'].sudo().search([('id', '=', order_id)])
        # # return str(so.access_token)
        # access_token = so.access_token
        try:
            order_sudo = self._document_check_access(
                'sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='sale.action_report_saleorder', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get('view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer')
            _message_post_helper(res_model='sale.order', res_id=order_sudo.id, message=body, token=order_sudo.access_token,
                                 message_type='notification', subtype="mail.mt_note", partner_ids=order_sudo.user_id.sudo().partner_id.ids)

        if request.env.user.partner_id.x_studio_approval_role == 'admin':
            isTeacher = True

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'isTeacher': isTeacher,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'usr': request.env.user.partner_id
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('website_published', '=', True),
                 ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('specific_countries', '=', False), ('country_ids',
                                                           'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                                                     (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search(
                [('partner_id', '=', order_sudo.partner_id.id),
                 ('acquirer_id', 'in', acquirers.filtered(lambda acq: acq.payment_flow == 's2s').ids)])

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render('ssi_cart.approved_page', values)

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
                if not so.access_token:
                    so.sudo().write({'access_token': str(uuid.uuid4())})
                data = {'message': 'Success', 'state': so.state}
            else:
                data = {'message': 'Failled'}
        except Exception:
            data = {'message': 'Failled'}
        return data

    @http.route(['/shop/cart/pendingcart'], 
      type='json', 
      auth="public", 
      methods=['POST'], 
      website=True, 
      multilang=False, 
      csrf=False)
    def pending_cart_custom(self,  **args):
        sale_order_id = request.session.get('sale_order_id')
        try:
            so = request.env['sale.order'].sudo().search([('id', '=', sale_order_id)], limit=1)
            if so:
                so.sudo().write({'state': 'pending'})
                if not so.access_token:
                    so.sudo().write({'access_token': str(uuid.uuid4())})
                data = {'message': 'Success', 'state': so.state}
            else:
                data = {'message': 'Failled'}
        except Exception:
            data = {'message': 'Failled'}
        return data
    