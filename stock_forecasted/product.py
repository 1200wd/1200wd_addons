# -*- coding: utf-8 -*-
##############################################################################
#
#    Stock Forecasted
#    Copyright (C) 2015 November
#    1200 Web Development
#    http://1200wd.com/
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
import logging

_logger = logging.getLogger(__name__)


class product_template(models.Model):
    _inherit = "product.template"

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute='_product_available',
                                  help="Forecasted quantity of products after delivery of orders.")

    @api.one
    def _product_available(self):
        cr = self.env.cr
        uid = self.env.uid
        context = self.env.context
        var_ids = []
        var_ids += [p.id for p in self.product_variant_ids]
        variant_available = self.pool['product.product']._product_available(cr, uid, var_ids, context=context)
        self.qty_forecasted = 0
        for p in self.product_variant_ids:
            self.qty_forecasted += variant_available[p.id]["qty_forecasted"]


class product_product(models.Model):
    _inherit = "product.product"

    qty_forecasted = fields.Float(string="Forecasted Stock", digits=dp.get_precision('Product Unit of Measure'),
                                  compute="_product_available_wrapper",
                                  help="Forecasted quantity of products after delivery of orders.")

    def _product_available_wrapper(self):
        res = self._product_available()
        for record in self:
            record.qty_forecasted = res[record.id]['qty_forecasted']


    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        context = context or {}
        _logger.debug("1200wd - Calculate forecasted stock")

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

        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            id = product.id
            qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            incoming_qty = float_round(moves_in.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            outgoing_qty = float_round(moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            virtual_available = float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            res[id] = {
                'qty_available': qty_available,
                'incoming_qty': incoming_qty,
                'outgoing_qty': outgoing_qty,
                'virtual_available': virtual_available,
                'qty_forecasted': qty_available - outgoing_qty,
            }
        return res