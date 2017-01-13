# -*- coding: utf-8 -*-
# © 2016 1200 WebDevelopment <1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
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
        """Set partner pricelist from sales channel."""
        if self.sales_channel_id.property_product_pricelist:
            self.property_product_pricelist = \
                    self.sales_channel_id.property_product_pricelist

    def _commercial_fields(self, cr, uid, context=None):
        return super(ResPartner, self)._commercial_fields(
            cr, uid, context=context
        ) + ['sales_channel_id']
