# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration
#    © 2016 - 1200 Web Development <http://1200wd.com/>
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


from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning


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
        context = context.copy() or {}
        sales = self.browse(cr, uid, ids, context=context)
        context['action_ship_create'] = sales
        r = super(SaleOrder, self).action_ship_create(cr, uid, ids, context=context)
        for sale in sales:
            sale.picking_ids.action_get_transsmart_rate()
        return r
