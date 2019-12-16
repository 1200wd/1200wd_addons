# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class TranssmartCostCenter(models.Model):
    """This model is used to hold the Cost Centers.

    the records of this model are created automatically by the synchronization
    operation and the user cannot change or create anything here.

    https://devdocs.transsmart.com/
    """
    _name = 'transsmart.cost.center'
    _description = "Transsmart Cost Center"

    transsmart_nr = fields.Integer(
        string='Identifier',
        required=True,
        index=True,
        oldname='transsmart_id',
    )
    transsmart_code = fields.Char(required=True, index=True, oldname='code')
    name = fields.Char()
    is_default = fields.Boolean()

    _sql_constraints = [
        ('transsmart_nr_unique', 'unique(transsmart_nr)',
         'Identifier field should be unique.')
    ]
