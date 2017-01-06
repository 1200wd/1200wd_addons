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


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        """Create invoice from stock.picking.
        
        Include customer sales channel and customer pricelist
        """
        inv_vals = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move
        )
        if 'partner_id' in inv_vals:
            partner = self.env['res.partner'].browse(inv_vals['partner_id'])
            if partner and partner.sales_channel_id:
                _logger.debug(
                    "1200wd - sale_channel - Create invoice from"
                    " stock.picking, use customer %s sales channel %s" %
                    (partner.id, partner.sales_channel_id.id)
                )
                price_list_id = (
                    partner.property_product_pricelist.id or
                    partner.sales_channel_id.property_product_pricelist.id or
                    False
                )
                inv_vals.update({
                    'sales_channel_id': partner.sales_channel_id.id,
                    'pricelist_id': price_list_id,
                })
            else:
                _logger.info(
                    "1200wd - sale_channel - Could not update sales channel,"
                    " partner has no sales channel defined. Vals %s" %
                    inv_vals
                )
        else:
            _logger.info(
                "1200wd - sale_channel - Could not update sales channel,"
                " partner not found. Vals %s" %
                inv_vals
            )
        return inv_vals
