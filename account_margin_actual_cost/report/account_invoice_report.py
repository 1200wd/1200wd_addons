# -*- coding: utf-8 -*-
#
#    Account Invoice - Actual Costs and Margins
#    © 1200 WebDevelopment <http://1200wd.com/>
#    2016 November
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

from openerp import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     help="Total Actual Costs of invoices")
    margin_avg = fields.Float(string="Margin % Average", readonly=True, digits=(16, 1),
                                     help="Average margin on invoices", group_operator="avg")

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """,
                    sub.actual_cost_total as actual_cost_total,
                    sub.margin_avg as margin_avg
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += """,
                    SUM(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - ail.actual_cost
                            ELSE ail.actual_cost
                        END) AS actual_cost_total,
                    avg(ai.margin_perc) as margin_avg
        """
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """,
                    ai.margin_perc
        """
        return group_by_str