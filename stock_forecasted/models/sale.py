# -*- coding: utf-8 -*-
##############################################################################
#
#    Stock Forecasted
#    1200 Web Development
#    http://1200wd.com/
#    Copyright (C) 2016 January
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

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Add index to sale order line on product_id and create_date
    product_id = fields.Many2one('product.product', 'Product', select=1)
    create_date = fields.Date('Created on', select=1)
