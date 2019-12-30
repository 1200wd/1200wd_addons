# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class TranssmartCostCenter(models.Model):
    """This model is used to hold the Cost Centers.

    the records of this model are created automatically by the synchronization
    operation and the user cannot change or create anything here.

    https://devdocs.transsmart.com/
    """
    _name = 'transsmart.cost.center'
    _description = "Transsmart Cost Center"

    transsmart_code = fields.Char(required=True, index=True, oldname='code')
    name = fields.Char()
    is_default = fields.Boolean()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('transsmart_code_unique',
         'unique(transsmart_code)',
         'Identifier field should be unique.')
    ]

    @api.multi
    def name_get(self):
        """Make code part of name."""
        result = []
        for this in self:
            name = super(TranssmartCostCenter, this).name_get()[0][1]
            if not name:
                result.append((this.id, this.transsmart_code))
            else:
                result.append((this.id, " -  ".join([this.transsmart_code, name])))
        return result
