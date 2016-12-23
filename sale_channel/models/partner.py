# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales Channels
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
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sales_channel_id = fields.Many2one(
        comodel_name='res.partner',
        string='Sales channel',
        ondelete='set null',
        domain="[('category_id', 'ilike', 'sales channel')]",
        index=True,
    )

    @api.onchange('sales_channel_id')
    def sales_channel_change(self):
        if self.sales_channel_id.property_product_pricelist:
            self.property_product_pricelist = \
                    self.sales_channel_id.property_product_pricelist
        if getattr(self, "_update_fiscal_position", False):
            self._update_fiscal_position()

    def _commercial_fields(self, cr, uid, context=None):
        return super(ResPartner, self)._commercial_fields(
            cr, uid, context=context
        ) + ['sales_channel_id']
