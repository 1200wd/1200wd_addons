# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    is_transsmart = fields.Boolean()
