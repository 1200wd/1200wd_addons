# -*- coding: utf-8 -*-
# © 2016 1200 WebDevelopment <1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        """Create invoice from stock.picking.

        Include customer sales channel
        """
        inv_vals = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move
        )
        if 'partner_id' in inv_vals:
            partner = self.env['res.partner'].browse(inv_vals['partner_id'])
            if partner and partner.sales_channel_id:
                inv_vals.update({
                    'sales_channel_id': partner.sales_channel_id.id,
                })
        return inv_vals
