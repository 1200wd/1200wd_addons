# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class TranssmartCarrier(models.Model):
    """This model is used to hold the carriers from Transsmart."""
    _name = 'transsmart.carrier'
    _description = "Transsmart Carrier"

    code = fields.Char(required=True, index=True)
    name = fields.Char()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique',
         'unique(code)',
         'Identifier field should be unique.')
    ]

    @api.multi
    def name_get(self):
        """Make code part of name."""
        result = []
        for this in self:
            name = super(TranssmartCarrier, this).name_get()[0][1]
            if not name:
                result.append((this.id, this.code))
            else:
                result.append((this.id, " -  ".join([this.code, name])))
        return result
