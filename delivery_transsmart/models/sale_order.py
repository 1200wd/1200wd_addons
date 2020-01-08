# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_service_level_time_id = fields.Many2one(
        comodel_name='delivery.service.level.time',
    )
    cost_center_id = fields.Many2one(
        comodel_name='transsmart.cost.center',
        string='Delivery Cost Center',
        readonly=True,
    )

    @api.multi
    def action_ship_create(self):
        """Set transsmart information on picking from service level and cost center."""
        package_model = self.env['delivery.package.type']
        default_package = package_model.get_default()
        result = super(SaleOrder, self).action_ship_create()
        for this in self:
            pickings = this.picking_ids
            pickings.write({
                'delivery_service_level_time_id':
                    this.delivery_service_level_time_id.id,
                'cost_center_id': this.cost_center_id.id,
                'package_type_id': default_package.id,
            })
            try:
                pickings.action_transsmart_get_rates()
            except Exception:  # pylint: disable=broad-except
                pass  # Ignore not being able to get rates now.
        return result
