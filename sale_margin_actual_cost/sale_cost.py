# -*- coding: utf-8 -*-
#
#    Sales - Actual Costs and Margins
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

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    @api.one
    @api.depends('actual_cost', 'price_unit', 'product_uos_qty')
    def get_actual_costs(self):
        if self.product_tmpl_id.actual_cost:
            self.actual_cost = 0
            self.actual_cost = self.product_tmpl_id.actual_cost * self.product_uos_qty
        if self.price_subtotal and self.actual_cost:
            self.margin_perc = ( 1 - ( self.actual_cost / self.price_subtotal ) ) * 100
        _logger.debug("1200wd - Sale order line {}: Update Actual Cost to {} and margin to {}".
                      format(self.id, self.actual_cost, self.margin_perc))
        return True

    actual_cost = fields.Float(string="Actual Cost Price", readonly=True,
                               compute="get_actual_costs", store=True,
                               digits_compute=dp.get_precision('Product Price'),
                               help="Actual costs of the products of this sale order line")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               compute="get_actual_costs", store=True,
                               help="Profit margin of this sale order line")

class sale_order(models.Model):
    _inherit = "sale.order"

    @api.one
    @api.depends('order_line')
    def calculate_total_actual_costs(self):
        self.actual_cost_total = 0
        for line in self.order_line:
            if line.state == 'cancel':
                continue
            self.actual_cost_total += line.actual_cost or 0.0
        if self.amount_untaxed and self.actual_cost_total:
            self.margin_perc = ( 1 - ( self.actual_cost_total / self.amount_untaxed) ) * 100
        _logger.debug("1200wd - Update sale.order actual costs to {} and margin to {}".
                      format(self.actual_cost_total, self.margin_perc))
        return True

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     digits_compute=dp.get_precision('Product Price'),
                                     compute="calculate_total_actual_costs", store=True,
                                     help="Actual Total Costs of the products of this sale order")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               compute="calculate_total_actual_costs", store=True,
                               help="Profit Margin of this sale order")