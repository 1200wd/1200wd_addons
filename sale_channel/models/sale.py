# -*- coding: utf-8 -*-
# © 2016 1200 WebDevelopment <1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sales_channel_id = fields.Many2one(
        comodel_name='res.partner',
        string='Sales channel',
        ondelete='set null',
        domain="[('category_id', 'ilike', 'sales channel')]",
        index=True,
    )

    @api.multi
    def onchange_partner_id(self, partner_id):
        """Add values from sales_channel partner, if available."""
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.sales_channel_id:
                res['value']['sales_channel_id'] = partner.sales_channel_id.id
        return res

    @api.model
    def _prepare_invoice(self, order, lines):
        """Make sure sales_channel_id is set on invoice."""
        val = super(SaleOrder, self)._prepare_invoice(order, lines)
        if order.sales_channel_id:
            val.update({
                'sales_channel_id': order.sales_channel_id.id,
            })
        return val
