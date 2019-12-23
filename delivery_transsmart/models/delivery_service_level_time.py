# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class DeliveryServiceLevelTime(models.Model):
    """
    Used for keeping the Service Level Time records.
    https://devdocs.transsmart.com/#_service_level_time_retrieval
    """
    _name = 'delivery.service.level.time'

    transsmart_code = fields.Char(required=True, index=True, oldname="code")
    name = fields.Char()
    pre_book = fields.Boolean(help="Available for prebooking")
    is_default = fields.Boolean()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('transsmart_code_unique',
         'unique(transsmart_code)',
         'Identifier field should be unique.')
    ]
