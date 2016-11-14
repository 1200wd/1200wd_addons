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

from openerp import models, fields, api


class SaleReport(models.Model):
    _inherit = "sale.report"

    actual_cost_total = fields.Float(string="Total Actual Cost", readonly=True,
                                     help="Actual Purchase Price for the product of this sale order line")

    def _select(self):
        select_str = super(SaleReport, self)._select()
        select_str += """,
                    sum(l.actual_cost) as actual_cost_total
        """
        return select_str
