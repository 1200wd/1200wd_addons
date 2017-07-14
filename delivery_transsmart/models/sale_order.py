# -*- coding: utf-8 -*-
# © 2016-2017 1200 Web Development <http://1200wd.com/>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import models, fields


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_service_level_time_id = fields.Many2one(
        'delivery.service.level.time',
        string='Delivery Service Level Time',
        ondelete="restrict")
    cost_center_id = fields.Many2one(
        'transsmart.cost.center',
        string='Delivery Cost Center')

    def action_ship_create(self, cr, uid, ids, context=None):
        context = context and context.copy() or {}
        sales = self.browse(cr, uid, ids, context=context)
        context['action_ship_create'] = sales
        result = super(SaleOrder, self).action_ship_create(
            cr, uid, ids, context=context
        )
        for sale in sales:
            try:
                # Should test beforehand wether transsmart applies. For
                # the moment surpress warning. Transsmart will be unlinked
                # from sales_order anyway:
                sale.picking_ids.action_get_transsmart_rate()
            except:
                _logger.info(
                    "Sale order %s not valid for transsmart" %
                    sale.display_name
                )
                pass
        return result
