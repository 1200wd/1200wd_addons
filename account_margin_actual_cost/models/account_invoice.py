# -*- coding: utf-8 -*-
#
#    Account Invoice - Actual Costs and Margins
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


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def calculate_actual_costs(self):
        for line in self:
            line.actual_cost = 0
            if line.invoice_id.type in ['out_invoice', 'out_refund']:
                if line.product_id.product_tmpl_id.actual_cost:
                    line.actual_cost = line.product_id.product_tmpl_id.actual_cost * line.quantity
                if line.price_subtotal and line.actual_cost:
                    line.margin_perc = ( 1 - (line.actual_cost / line.price_subtotal) ) * 100
            # _logger.debug("1200wd - Invoice line {}: Update Actual Cost to {} and margin to {}%".
            #               format(self.id, self.actual_cost, self.margin_perc))

    actual_cost = fields.Float(string="Actual Cost Price", readonly=True,
                               digits=dp.get_precision('Product Price'),
                               help="Actual Purchase Price for the product of this invoice line")
    discount = fields.Float(group_operator="avg")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               help="Profit margin of this invoice line")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def calculate_total_actual_costs(self):
        for invoice in self:
            invoice.actual_cost_total = 0
            invoice.margin_perc = 0
            if invoice.type in ['out_invoice', 'out_refund']:
                for line in invoice.invoice_line:
                    line.calculate_actual_costs()
                    invoice.actual_cost_total += line.actual_cost or 0.0
                if invoice.amount_untaxed and invoice.actual_cost_total:
                    invoice.margin_perc = ( 1 - ( invoice.actual_cost_total / invoice.amount_untaxed) ) * 100
                _logger.debug("1200wd - Update invoice total actual costs {} and margin to {}%".
                              format(invoice.actual_cost_total, invoice.margin_perc))

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     digits=dp.get_precision('Product Price'),
                                     help="Total Actual costs of this invoice, excluding tax")
    margin_perc = fields.Float(string="Margin %", readonly=True,
                               digits=(16, 1), group_operator="avg",
                               help="Profit margin of this invoice")

    @api.multi
    def write(self, vals):
        super(AccountInvoice, self).write(vals)
        if 'invoice_line' in vals:
            for inv in self:
                inv.calculate_total_actual_costs()
        return True

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if 'invoice_line' in vals:
            res.calculate_total_actual_costs()
        return res
