# -*- coding: utf-8 -*-
# Copyright 2020 - Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields
from odoo.http import request
from odoo import http, tools
from odoo.addons.portal.controllers.portal import CustomerPortal, pager

_logger = logging.getLogger(__name__)


class BookingsCustom(http.Controller):
    """booking custom"""

    @http.route(['/freight/shipment/booking/create'], type='http', auth='user', website=True,
                cache=300, csrf=False)
    def portal_my_bookings_create(self):
        """portal my booking create"""
        shipper = request.env['res.partner'].sudo().search([('shipper', '=', True)])
        consignee = request.env['res.partner'].search([('consignee', '=', True)])
        users = request.env['res.users'].search([])
        gateways = request.env['freight.port'].search([])
        values = {
            'shipper': shipper,
            'consignee': consignee,
            'users': users,
            'gateways': gateways,
        }
        return request.render("tk_freight.portal_booking_create", values)

    @http.route(['/freight/shipment/booking/submit'], type='http', auth='user', website=True,
                cache=300, csrf=False)
    def portal_my_bookings_submit(self, **post):
        """portal my bookings submit"""
        operation = request.env['shipment.quotation']
        final_dict = {}
        if post:
            if post.get('operation'):
                final_dict['operation'] = post.get('operation')
            if post.get('transport'):
                final_dict['transport'] = post.get('transport')
            final_dict['consignee_id'] = request.env.user.partner_id.id
            if post.get('source'):
                final_dict['source'] = post.get('source')
            if post.get('destination'):
                final_dict['destination'] = post.get('destination')
            if post.get('notes'):
                final_dict['notes'] = post.get('notes')
            if post.get('length'):
                final_dict['length'] = post.get('length')
            if post.get('height'):
                final_dict['height'] = post.get('height')
            if post.get('weight'):
                final_dict['weight'] = post.get('weight')
            if post.get('width'):
                final_dict['width'] = post.get('width')
            if post.get('danger') == 'on':
                final_dict['dangerous_goods'] = True
                if 'danger_info' in post:
                    final_dict['dangerous_goods_notes'] = post.get(
                        'danger_info')
        final_dict['address_to'] = 'location_address'
        final_dict['from_booking'] = True
        booking = operation.sudo().create(final_dict)
        return request.render("tk_freight.portal_booking_create_thankyou", {'operation': booking})

    @http.route(['/freight/shipment/booking'], type='http', auth="user", website=True, cache=300)
    def portal_my_bookings(self):
        """portal my bookings"""

        bookings = request.env['shipment.freight.booking']
        # make pager
        values = {}
        domain = ['|', ('create_uid', '=', False), ('create_uid', '=', request.env.user.id)]
        bookings_recs = bookings.search(domain)
        values.update({
            'bookings': bookings_recs.sudo(),
        })
        return request.render("tk_freight.portal_my_bookings", values)

    @http.route(['/freight/shipment/booking/details/<model("shipment.freight.booking"):booking>'],
                type='http', auth="user", website=True, cache=300)
    def portal_my_booking_detail(self, booking):
        """portal my booking detail"""
        prev_url = None
        next_url = None

        bookings = request.env['shipment.freight.booking']
        domain = [('consignee_id', '=', request.env.user.partner_id.id)]
        bookings_recs = bookings.sudo().search(domain)

        track_ids = request.env['booking.line'].sudo().search(
            [('booking_id', '=', booking.id)], order='id DESC')
        bookings_recs_ids = bookings_recs.ids
        order_index = bookings_recs_ids.index(booking.id)
        if order_index != 0 and bookings_recs_ids[order_index - 1]:
            prev_url = f"/freight/shipment/booking/details/{bookings_recs_ids[order_index - 1]}"
        if order_index < len(bookings_recs_ids) - 1 and bookings_recs_ids[order_index + 1]:
            next_url = f"/freight/shipment/booking/details/{bookings_recs_ids[order_index + 1]}"
        values = {
            'booking': booking.sudo(),
            'track_ids': track_ids,
            'page_name': 'portal_booking_form_view',
            "prev_record": prev_url,
            "next_record": next_url,
        }
        return request.render("tk_freight.portal_my_booking_detail", values)

    @http.route(['/freight/shipment/quotation/details/<model("shipment.quotation"):q>'],
                type='http', auth="user", website=True, cache=300)
    def portal_my_quotation_detail(self, q):
        """portal my quotation detail"""
        prev_url = None
        next_url = None

        quotation = request.env['shipment.quotation']
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]
        quot_recs = quotation.sudo().search(domain)
        quot_recs_ids = quot_recs.ids
        order_index = quot_recs_ids.index(q.id)
        if order_index != 0 and quot_recs_ids[order_index - 1]:
            prev_url = f"/freight/shipment/quotation/details/{quot_recs_ids[order_index - 1]}"
        if order_index < len(quot_recs_ids) - 1 and quot_recs_ids[order_index + 1]:
            next_url = f"/freight/shipment/quotation/details/{quot_recs_ids[order_index + 1]}"

        values = {
            'quot': q.sudo(),
            'page_name': 'portal_quotation_form_view',
            "prev_record": prev_url,
            "next_record": next_url,
        }
        return request.render("tk_freight.portal_my_quotation_detail", values)

    @http.route(['/freight/shipment/bookings', '/freight/shipment/bookings/page/<int:page>'],
                type='http', auth="user", website=True)
    def booking_details(self, page=1):
        """booking details"""
        bookings = request.env['shipment.freight.booking']
        values = {}
        domain = [('consignee_id', '=', request.env.user.partner_id.id)]

        total_orders = bookings.sudo().search_count(domain)
        page_details = request.website.pager(url="/freight/shipment/bookings",
                                             total=total_orders, page=page, step=10)
        bookings_recs = bookings.sudo().search(domain, limit=10, offset=page_details['offset'])

        values.update({
            'bookings': bookings_recs.sudo(),
            'page_name': 'bookings_list_page',
            "pager": page_details,
        })
        return request.render("tk_freight.booking_details", values)

    @http.route(['/freight/shipment/quotation', '/freight/shipment/quotation/page/<int:page>'],
                type='http', auth="user", website=True)
    def quotation_details(self, page=1):
        """quotation details"""
        quotation = request.env['shipment.quotation']
        values = {}
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]

        total_orders = quotation.sudo().search_count(domain)
        page_details = pager(url="/freight/shipment/quotation",
                             total=total_orders, page=page, step=10)
        quot_recs = quotation.search(domain, limit=10, offset=page_details['offset'])

        values.update({
            'quot': quot_recs.sudo(),
            'page_name': 'quotations_list_page',
            'pager': page_details,
        })
        return request.render("tk_freight.quotation_detail", values)

    @http.route(['/post/comment'], type='http', auth="user", website=True)
    def post_comment(self, **kw):
        """post comment"""
        book_id = request.env['shipment.freight.booking'].sudo().browse(
            int(kw['book_id']))
        vals = {'name': tools.ustr(kw['comment']),
                'user_id': request.env.user.id,
                'date': fields.datetime.now(),
                'booking_id': book_id.id}
        request.env['booking.line'].sudo().create(vals)
        track_ids = request.env['booking.line'].sudo().search(
            [('booking_id', '=', book_id.id)], order='id DESC')
        body = f'Note:{tools.ustr(kw["comment"])} noted by {request.env.user.partner_id.name}'
        book_id.sudo().message_post(body=body)
        values = {}
        values.update({
            'booking': book_id.sudo(),
            'track_ids': track_ids,
        })
        return request.render("tk_freight.portal_my_booking_detail", values)

    @http.route(['/shipment'], type='http', auth="public", website=True)
    def track_freight(self):
        """track freight"""
        return request.render('tk_freight.track_shipment')

    @http.route(['/track/shipment', '/track/shipment/<string:booking>',
                 '/track/shipment/<string:shipment>'], type='http', auth="public", website=True)
    def track_shipment(self, booking=None):
        """track shipment"""
        tracking_no = request.params.get('q')
        if not tracking_no:
            return request.redirect('/shipment')
        freight = request.env['freight.shipment'].sudo().search(
            [('name', '=', tracking_no)])
        if freight:
            page_name = "no_page"
            if booking == 'booking':
                page_name = 'tracking_bookings_shipment'
            elif booking == 'shipment':
                page_name = 'tracking_shipments_shipment'
            return request.render('tk_freight.freight_success',
                                  {'freight': freight, 'page_name': page_name})
        return request.redirect('/shipment')

    @http.route(['/freight/shipment/shipment', '/freight/shipment/shipment/page.<int:page>'],
                type='http', auth="user",
                website=True)
    def shipment_details(self, page=1):
        """shipment details"""
        shipment = request.env['freight.shipment']
        values = {}
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]
        shipment = shipment.search(domain)

        total_orders = shipment.sudo().search_count(domain)

        page_details = pager(url="/freight/shipment/shipment", total=total_orders, page=page,
                             step=10)
        shipment = shipment.search(domain, limit=10, offset=page_details['offset'])

        values.update({
            'shipments': shipment.sudo(),
            'page_name': 'shipments_list_page',
            "pager": page_details,
        })
        return request.render("tk_freight.shipment_details", values)

    @http.route(['/freight/shipment/shipment/details/<model("freight.shipment"):s>'], type='http',
                auth="user", website=True, cache=300)
    def portal_my_shipment_detail(self, s):
        """portal my shipment detail"""
        prev_url = None
        next_url = None

        shipment = request.env['freight.shipment']
        domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                  ('shipper_id', '=', request.env.user.partner_id.id)]
        shipment = shipment.search(domain)

        shipment_ids = shipment.ids
        order_index = shipment_ids.index(s.id)
        if order_index != 0 and shipment_ids[order_index - 1]:
            prev_url = f"/freight/shipment/shipment/details/{shipment_ids[order_index - 1]}"
        if order_index < len(shipment_ids) - 1 and shipment_ids[order_index + 1]:
            next_url = f"/freight/shipment/shipment/details/{shipment_ids[order_index + 1]}"

        values = {
            'shipment': s.sudo(),
            'page_name': 'portal_shipments_form_view',
            "prev_record": prev_url,
            "next_record": next_url,
        }
        return request.render("tk_freight.portal_my_shipment_details", values)


class FreightCustomerPortal(CustomerPortal):
    """freight customer portal"""

    def _prepare_home_portal_values(self, counters):
        """prepare home portal values"""
        values = super()._prepare_home_portal_values(counters)
        bookings = request.env['shipment.freight.booking']
        domain = [('consignee_id', '=', request.env.user.partner_id.id)]
        if 'freight_count' in counters:
            values['freight_count'] = bookings.search_count(domain)
        shipment = request.env['freight.shipment']
        shipment_domain = ['|', ('consignee_id', '=', request.env.user.partner_id.id),
                           ('shipper_id', '=', request.env.user.partner_id.id)]
        if 'quotation_count' in counters:
            values['quotation_count'] = request.env['shipment.quotation'].search_count(
                shipment_domain)
        if 'shipment_count' in counters:
            values['shipment_count'] = shipment.search_count(shipment_domain)
        return values
