# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_level_time_id = fields.Many2one('service.level.time')

    @api.multi
    def action_ship_create(self):
        result = super(SaleOrder, self).action_ship_create()
        for rec in self:
            rec.picking_ids.write({
                'service_level_time_id': rec.service_level_time_id.id,
            })
        return result
