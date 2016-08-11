# -*- coding: utf-8 -*-
##############################################################################
#
#    Stock Forecasted
#    1200 Web Development
#    http://1200wd.com/
#    Copyright (C) 2016 August
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
import datetime
import logging

_logger = logging.getLogger(__name__)

days_reserve_sales = 31


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def _product_available(self, name=None, arg=False):
        start = datetime.datetime.now()
        res = {}
        var_ids = []
        for product in self:
            var_ids += [p.id for p in product.product_variant_ids]
        variant_available = self.env['product.product'].browse(var_ids)._product_available()

        for product in self:
            product.qty_available = 0
            product.virtual_available = 0
            product.incoming_qty = 0
            product.outgoing_qty = 0
            product.qty_forecasted = 0
            product.outgoing_sales_qty = 0
            for p in product.product_variant_ids:
                product.qty_available += variant_available[p.id]["qty_available"]
                product.virtual_available += variant_available[p.id]["virtual_available"]
                product.incoming_qty += variant_available[p.id]["incoming_qty"]
                product.outgoing_qty += variant_available[p.id]["outgoing_qty"]
                product.qty_forecasted += variant_available[p.id]['qty_forecasted']
                product.outgoing_sales_qty += variant_available[p.id]['outgoing_sales_qty']

            res[product.id] = {
                "qty_available": product.qty_available,
                "virtual_available": product.virtual_available,
                "incoming_qty": product.incoming_qty,
                "outgoing_qty": product.outgoing_qty,
                "qty_forecasted": product.qty_forecasted,
                "outgoing_sales_qty": product.outgoing_sales_qty,
            }
        _logger.debug("1200wd - ProductTemplate._product_available, products %d, TOTAL execution time %dms" % (len(res), (datetime.datetime.now()-start).total_seconds()*1000))

        return res

    def _search_qty_forecasted(self, operator, value):
        domain = [('qty_forecasted', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Forecasted quantity of products after delivery of orders.")
    outgoing_sales_qty = fields.Float(string="Outgoing Sales", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Expected outgoing sales. Quantity is based on a certain percentage of recent sales orders.")

    def action_view_pending_sale_order_lines(self, cr, uid, ids, context=None):
        global days_reserve_sales
        products = self._get_products(cr, uid, ids, context=context)
        result = self._get_act_window_dict(cr, uid, 'stock_forecasted.action_order_line_product_tree_forecasted', context=context)

        date_from = ((datetime.datetime.now() - datetime.timedelta(days=days_reserve_sales)).strftime('%Y-%m-%d'))
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, products)) + "])," \
            "('state', 'not in', ('cancel', 'done')), ('create_date', '>=', '" + date_from + "')]"

        return result

    def action_view_outgoing_stock_moves(self, cr, uid, ids, context=None):
        products = self._get_products(cr, uid, ids, context=context)
        result = self._get_act_window_dict(cr, uid, 'stock_forecasted.action_stock_move_outgoing_tree_forecasted', context=context)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self.env['product.product']._get_domain_locations(cr, uid, products, context=context)

        result['domain'] = "[('product_id','in',[" + ','.join(map(str, products)) + "])," \
            "('state', 'not in', ('draft', 'cancel', 'done')), " + str(domain_move_out_loc)[1:][:-1] + "]"

        return result


class ProductProduct(models.Model):
    _inherit = "product.product"

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Forecasted product quantity. Based on incoming and outgoing stock moves and pending sales orders.")
    outgoing_sales_qty = fields.Float(string="Outgoing Sales", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Expected outgoing sales. Quantity is based on a certain percentage of recent sales orders.")

    @api.multi
    def _product_available(self):
        tstart = datetime.datetime.now()
        global days_reserve_sales

        domain_products = [('product_id', 'in', self.ids)]
        domain_quant, domain_move_in, domain_move_out = [], [], []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_move_in += self._get_domain_dates() + \
            [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self._get_domain_dates() + \
            [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products

        if self._context.get('lot_id'):
            domain_quant.append(('lot_id', '=', self._context['lot_id']))
        if self._context.get('owner_id'):
            domain_quant.append(('owner_id', '=', self._context['owner_id']))
            owner_domain = ('restrict_partner_id', '=', self._context['owner_id'])
            domain_move_in.append(owner_domain)
            domain_move_out.append(owner_domain)
        if self._context.get('package_id'):
            domain_quant.append(('package_id', '=', self._context['package_id']))

        domain_move_in += domain_move_in_loc
        domain_move_out += domain_move_out_loc
        moves_in = self.env['stock.move'].read_group(
            domain=domain_move_in, fields=['product_id', 'product_qty'], groupby=['product_id'])
        moves_out = self.env['stock.move'].read_group(
            domain=domain_move_out, fields=['product_id', 'product_qty'], groupby=['product_id'])

        domain_quant += domain_quant_loc
        quants = self.env['stock.quant'].read_group(domain=domain_quant, fields=['product_id', 'qty'], groupby=['product_id'])
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))

        t1 = datetime.datetime.now()
        # Get pending sales
        domain_sales_date = \
            [('create_date', '>=', ((tstart - datetime.timedelta(days=days_reserve_sales)).strftime('%Y-%m-%d')))]
        domain_sales_out = domain_sales_date + [('state', 'not in', ('cancel', 'done'))] + domain_products
        sales_out = self.env['sale.order.line'].read_group(
            domain_sales_out, ['product_id', 'product_uos_qty'], ['product_id'])
        sales_out = dict(map(lambda x: (x['product_id'][0], x['product_uos_qty']), sales_out))
        _logger.debug("1200wd - ProductProduct number of pending sales %s" % len(sales_out))

        t2 = datetime.datetime.now()

        # Get almost incoming products
        domain_move_in_expected = domain_move_in + [('date_expected', '<=', ((tstart + datetime.timedelta(days=2)).strftime('%Y-%m-%d')))]
        import pdb; pdb.set_trace()
        moves_in_expected = self.env['stock.move'].read_group(domain_move_in_expected, ['product_id', 'product_qty'], ['product_id'])
        moves_in_expected = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in_expected))
        _logger.debug("1200wd - ProductProduct number of moves_in_expected %s" % len(moves_in_expected))

        t3 = datetime.datetime.now()
        res = {}
        for product in self:
            id = product.id
            product.qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.incoming_qty = float_round(moves_in.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.outgoing_qty = float_round(moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.outgoing_sales_qty = float_round(sales_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.virtual_available = \
                float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) -
                            moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            in_expected = float_round(moves_in_expected.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.qty_forecasted = \
                product.qty_available - (product.outgoing_qty + product.outgoing_sales_qty) + in_expected

            res[id] = {
                'qty_available': product.qty_available,
                'incoming_qty': product.incoming_qty,
                'outgoing_qty': product.outgoing_qty,
                'virtual_available': product.virtual_available,
                'qty_forecasted': product.qty_forecasted,
                'outgoing_sales_qty': product.outgoing_sales_qty,
            }
        extimes = "Execution times t1, t2, t3, total: %dms, %dms, %dms, %dms" % (
            ((t1-tstart).total_seconds()*1000),
            ((t2-tstart).total_seconds()*1000),
            ((t3-tstart).total_seconds()*1000),
            ((datetime.datetime.now()-tstart).total_seconds()*1000),)
        _logger.debug("1200wd - ProductProduct._product_available, products %d" % (len(res)))
        _logger.debug("1200wd - Execution times %s" % extimes)
        return res

    def action_view_pending_sale_order_lines(self, cr, uid, ids, context=None):
        global days_reserve_sales
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.env['product.template']._get_act_window_dict(cr, uid, 'stock_forecasted.action_order_line_product_tree_forecasted', context=context)

        date_from = ((datetime.datetime.now() - datetime.timedelta(days=days_reserve_sales)).strftime('%Y-%m-%d'))
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])," \
            "('state', 'not in', ('cancel', 'done')), ('create_date', '>=', '" + date_from + "')]"

        return result

    def action_view_outgoing_stock_moves(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.env['product.template']._get_act_window_dict(cr, uid, 'stock_forecasted.action_stock_move_outgoing_tree_forecasted', context=context)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)

        result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])," \
            "('state', 'not in', ('draft', 'cancel', 'done')), " + str(domain_move_out_loc)[1:][:-1] + "]"

        return result
