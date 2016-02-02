# -*- coding: utf-8 -*-
##############################################################################
#
#    Stock Forecasted
#    1200 Web Development
#    http://1200wd.com/
#    Copyright (C) 2016 February
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


    def _product_available(self, cr, uid, ids, name=None, arg=False, context=None):
        prod_available = {}
        product_ids = self.browse(cr, uid, ids, context=context)
        var_ids = []
        for product in product_ids:
            var_ids += [p.id for p in product.product_variant_ids]
        variant_available = self.pool['product.product']._product_available(cr, uid, var_ids, context=context)

        for product in product_ids:
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

            prod_available[product.id] = {
                "qty_available": product.qty_available,
                "virtual_available": product.virtual_available,
                "incoming_qty": product.incoming_qty,
                "outgoing_qty": product.outgoing_qty,
                "qty_forecasted": product.qty_forecasted,
                "outgoing_sales_qty": product.outgoing_sales_qty,
            }
        _logger.debug("1200wd - ProductTemplate._product_available, product ids %s, result %s" % (product_ids,prod_available))
        return prod_available

    def _search_qty_forecasted(self, operator, value):
        domain = [('qty_forecasted', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available', search='_search_qty_forecasted',
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
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self.pool['product.product']._get_domain_locations(cr, uid, products, context=context)

        result['domain'] = "[('product_id','in',[" + ','.join(map(str, products)) + "])," \
            "('state', 'not in', ('draft', 'cancel', 'done')), " + str(domain_move_out_loc)[1:][:-1] + "]"

        return result


class ProductProduct(models.Model):
    _inherit = "product.product"

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available', store=True,
                                  help="Forecasted product quantity. Based on incoming and outgoing stock moves and pending sales orders.")
    outgoing_sales_qty = fields.Float(string="Outgoing Sales", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Expected outgoing sales. Quantity is based on a certain percentage of recent sales orders.")

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        global days_reserve_sales
        context = context or {}

        domain_products = [('product_id', 'in', ids)]
        domain_quant, domain_move_in, domain_move_out = [], [], []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)
        domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products

        if context.get('lot_id'):
            domain_quant.append(('lot_id', '=', context['lot_id']))
        if context.get('owner_id'):
            domain_quant.append(('owner_id', '=', context['owner_id']))
            owner_domain = ('restrict_partner_id', '=', context['owner_id'])
            domain_move_in.append(owner_domain)
            domain_move_out.append(owner_domain)
        if context.get('package_id'):
            domain_quant.append(('package_id', '=', context['package_id']))

        domain_move_in += domain_move_in_loc
        domain_move_out += domain_move_out_loc
        moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty'], ['product_id'], context=context)
        moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty'], ['product_id'], context=context)

        domain_quant += domain_quant_loc
        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant, ['product_id', 'qty'], ['product_id'], context=context)
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))

        # Get pending sales
        now = datetime.datetime.now()
        domain_sales_date = [('create_date', '>=', ((now - datetime.timedelta(days=days_reserve_sales)).strftime('%Y-%m-%d')))]
        domain_sales_out = domain_sales_date + [('state', 'not in', ('cancel', 'done'))] + domain_products
        sales_out = self.pool.get('sale.order.line').read_group(cr, uid, domain_sales_out, ['product_id', 'product_uos_qty'], ['product_id'], context=context)
        sales_out = dict(map(lambda x: (x['product_id'][0], x['product_uos_qty']), sales_out))
        _logger.debug("1200wd - Product %s pending sales %s (total execution time %dms)" % (ids, sales_out, (datetime.datetime.now()-now).total_seconds()*1000))

        # Get almost incoming products
        domain_move_in_expected = domain_move_in + [('date_expected', '<=', ((now + datetime.timedelta(days=2)).strftime('%Y-%m-%d')))]
        moves_in_expected = self.pool.get('stock.move').read_group(cr, uid, domain_move_in_expected, ['product_id', 'product_qty'], ['product_id'], context=context)
        moves_in_expected = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in_expected))

        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            id = product.id
            product.qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.incoming_qty = float_round(moves_in.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.outgoing_qty = float_round(moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.outgoing_sales_qty = float_round(sales_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.virtual_available = float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            in_expected = float_round(moves_in_expected.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            product.qty_forecasted = product.qty_available - (product.outgoing_qty + product.outgoing_sales_qty) + in_expected

            res[id] = {
                'qty_available': product.qty_available,
                'incoming_qty': product.incoming_qty,
                'outgoing_qty': product.outgoing_qty,
                'virtual_available': product.virtual_available,
                'qty_forecasted': product.qty_forecasted,
                'outgoing_sales_qty': product.outgoing_sales_qty,
            }
        _logger.debug("1200wd - ProductProduct._product_available, product ids %s, result %s" % (ids, res))
        return res

    def action_view_pending_sale_order_lines(self, cr, uid, ids, context=None):
        global days_reserve_sales
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.pool['product.template']._get_act_window_dict(cr, uid, 'stock_forecasted.action_order_line_product_tree_forecasted', context=context)

        date_from = ((datetime.datetime.now() - datetime.timedelta(days=days_reserve_sales)).strftime('%Y-%m-%d'))
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])," \
            "('state', 'not in', ('cancel', 'done')), ('create_date', '>=', '" + date_from + "')]"

        return result

    def action_view_outgoing_stock_moves(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.pool['product.template']._get_act_window_dict(cr, uid, 'stock_forecasted.action_stock_move_outgoing_tree_forecasted', context=context)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)

        result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])," \
            "('state', 'not in', ('draft', 'cancel', 'done')), " + str(domain_move_out_loc)[1:][:-1] + "]"

        return result
