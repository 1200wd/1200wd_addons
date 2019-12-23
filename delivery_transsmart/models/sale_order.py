# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_service_level_time_id = fields.Many2one(
        comodel_name='delivery.service.level.time',
        oldname='service_level_time_id',
    )

    @api.multi
    def action_ship_create(self):
        """Set transsmart information on picking from service level."""
        result = super(SaleOrder, self).action_ship_create()
        for this in self:
            this.picking_ids.write({
                'delivery_service_level_time_id': this.delivery_service_level_time.id,
            })
        return result
