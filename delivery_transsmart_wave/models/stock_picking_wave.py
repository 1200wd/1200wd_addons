# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockPickingWave(models.Model):
    _inherit = "stock.picking.wave"

    @api.multi
    def action_transsmart_book_shipping(self):
        for rec in self:
            rec.picking_ids.action_transsmart_book_shipping()
