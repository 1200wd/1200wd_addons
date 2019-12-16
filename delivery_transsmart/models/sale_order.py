# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_level_time_id = fields.Many2one(
        comodel_name='service.level.time',
        oldname='delivery_service_level_time_id',
    )

    @api.multi
    def action_ship_create(self):
        """Set transsmart information on picking from service level."""
        result = super(SaleOrder, self).action_ship_create()
        profile_model = self.env['booking.profile']
        for this in self:
            # Set booking profile to the first one with a corresponding
            # service level time id.
            service_level = this.service_level_time_id
            profile = profile_model.search(
                [('service_level_time_id', '=', service_level.id)],
                limit=1
            )
            this.picking_ids.write({
                'booking_profile_id': profile.id,
                'service_level_time_id': service_level.id,
            })
        return result
