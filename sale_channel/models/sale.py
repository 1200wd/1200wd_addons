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
import logging
from openerp import models, fields, api, _


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
            self.pricelist_id = \
                self.sales_channel_id.property_product_pricelist

    @api.multi
    def onchange_partner_id(self, partner_id):
        """Add values from sales_channel partner, if available."""
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.sales_channel_id:
                res['value']['sales_channel_id'] = partner.sales_channel_id
                if partner.sales_channel_id.property_product_pricelist:
                    res['value']['pricelist_id'] = \
                        partner.sales_channel_id.property_product_pricelist
        return res

    @api.model
    def _prepare_invoice(self, order, lines, context=None):
        _logger.debug('1200wd sale_channel prepare_invoice')
        val = super(SaleOrder, self)._prepare_invoice(
            order, lines, context=context
        )
        if order.sales_channel_id:
            val.update({
                'sales_channel_id': order.sales_channel_id.id,
            })
        return val
