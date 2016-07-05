# -*- coding: utf-8 -*-
#
#    Account Invoice - Actual Costs and Margins
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


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('actual_cost', 'quantity', 'price_subtotal')
    def get_actual_costs(self):
        self.actual_cost = 0
        if self.invoice_id.type not in ['out_invoice', 'out_refund']:
            return
        if self.product_id.product_tmpl_id.actual_cost:
            self.actual_cost = self.product_id.product_tmpl_id.actual_cost * self.quantity
        if self.price_subtotal and self.actual_cost:
            self.margin_perc = ( 1 - (self.actual_cost / self.price_subtotal) ) * 100
        _logger.debug("1200wd - Invoice line {}: Update Actual Cost to {} and margin to {}%".
                      format(self.id, self.actual_cost, self.margin_perc))
        return True

    actual_cost = fields.Float(string="Actual Cost Price", readonly=True,
                               compute="get_actual_costs", store=True,
                               digits_compute=dp.get_precision('Product Price'),
                               help="Actual Purchase Price for the product of this invoice line")
    discount = fields.Float(group_operator="avg")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               compute="get_actual_costs", store=True,
                               help="Profit margin of this invoice line")


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line')
    def calculate_total_actual_costs(self):
        self.actual_cost_total = 0
        self.margin_perc = 0
        if self.type not in ['out_invoice', 'out_refund']:
            return
        for line in self.invoice_line:
            line.get_actual_costs()
            self.actual_cost_total += line.actual_cost or 0.0
        if self.amount_untaxed and self.actual_cost_total:
            self.margin_perc = ( 1 - ( self.actual_cost_total / self.amount_untaxed) ) * 100
        _logger.debug("1200wd - Update invoice total actual costs {} and margin to {}%".
                      format(self.actual_cost_total, self.margin_perc))
        return True

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     digits_compute=dp.get_precision('Product Price'),
                                     compute="calculate_total_actual_costs", store=True,
                                     help="Total Actual costs of this invoice, excluding tax")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               compute="calculate_total_actual_costs", store=True,
                               help="Profit margin of this invoice")
