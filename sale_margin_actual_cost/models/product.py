# -*- coding: utf-8 -*-
#
#    Sales - Actual Costs and Margins
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

from openerp import models, fields, api, exceptions, _


# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#
#     cost_method = fields.Selection(
#         [('standard', 'Standard Price'), ('average', 'Average Price'),
#          ('real', 'Real Price'), ('actual', 'Actual Price')],
#         help="""Standard Price: The cost price is manually updated at the end of a specific period (usually every year).
#                 Average Price: The cost price is recomputed at each incoming shipment and used for the product valuation.
#                 Real Price: The cost price displayed is the price of the last outgoing product (will be use in case of inventory loss for example).
#                 Actual Price: The actual price is based on the 'cost price' plus extra manual determined costs.
#                 """,
#         string="Costing Method", required=True, copy=True)