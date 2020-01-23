# -*- coding: utf-8 -*-
# Copyright 2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockPickingRate(models.Model):
    """Rates can be retrieved for a stock picking for debugging purposes."""

    _name = "stock.picking.rate"
    _description = "Transsmart rate for stock picking."

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        readonly=True,
    )
    name = fields.Char(readonly=True)
    price = fields.Float(digits=(9, 2), readonly=True)
