# -*- coding: utf-8 -*-
##############################################################################
#
#    Product Price History View
#    Copyright (C) 2016 April
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

from openerp import models, api, fields

class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'

    # Add index to product field
    product_template_id = fields.Many2one('product.template', 'Product Template', required=True, ondelete='cascade', index=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    def compute_price_history_count(self):
        self.price_history_count = self.env['product.price.history'].search_count([('product_template_id', '=', self.id)])

    price_history_count = fields.Integer("Price History Count", compute='compute_price_history_count')