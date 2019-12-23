# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class TranssmartCarrier(models.Model):
    """This model is used to hold the carriers from Transsmart."""
    _name = 'transsmart.carrier'
    _description = "Transsmart Carrier"

    transsmart_code = fields.Char(required=True, index=True)
    name = fields.Char()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('transsmart_code_unique',
         'unique(transsmart_code)',
         'Identifier field should be unique.')
    ]
