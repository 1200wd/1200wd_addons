# -*- coding: utf-8 -*-
#
#    Sales - Actual Costs and Margins
#    © 2016 - 1200 WebDevelopment <http://1200wd.com/>
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def calculate_actual_costs(self):
        for line in self:
            if line.product_tmpl_id.actual_cost:
                line.actual_cost = line.product_tmpl_id.actual_cost * line.product_uos_qty
            if line.price_subtotal and line.actual_cost:
                line.margin_perc = ( 1 - ( line.actual_cost / line.price_subtotal ) ) * 100

    actual_cost = fields.Float(string="Actual Cost Price", readonly=True,
                               compute="calculate_actual_costs", store=True,
                               digits_compute=dp.get_precision('Product Price'),
                               help="Actual costs of the products of this sale order line")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               compute="calculate_actual_costs", store=True,
                               help="Profit margin of this sale order line")

    # @api.model
    # def create(self, vals):
    #     res = super(SaleOrderLine, self).create(vals)
    #     # TODO: This shouldn't be neccesary?
    #     res.calculate_actual_costs()
    #     return res

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def calculate_total_actual_costs(self):
        for sale in self:
            actual_cost_total = 0
            for line in sale.order_line:
                if line.state == 'cancel':
                    continue
                line.calculate_actual_costs()
                actual_cost_total += line.actual_cost or 0.0
            if sale.amount_untaxed and sale.actual_cost_total:
                sale.margin_perc = ( 1 - ( actual_cost_total / sale.amount_untaxed) ) * 100
            sale.actual_cost_total = actual_cost_total
            _logger.debug("1200wd - Update sale.order actual costs to {} and margin to {}".
                          format(actual_cost_total, sale.margin_perc))

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     digits=dp.get_precision('Product Price'),
                                     help="Actual Total Costs of the products of this sale order")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               help="Profit Margin of this sale order")


    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'order_line' in vals:
            for sale in self:
                sale.calculate_total_actual_costs()
        return res


    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if 'order_line' in vals:
            res.calculate_total_actual_costs()
        return res
