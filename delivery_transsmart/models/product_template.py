# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ProductTemplate(models.Model):
    """
    This model is used to hold the package types.
    https://devdocs.transsmart.com/#_packages_retrieval
    """
    _inherit = 'product.template'

    transsmart_nr = fields.Integer('Identifier', index=True)
    transsmart_code = fields.Char()
    package_type = fields.Char()
    package = fields.Boolean()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    is_default = fields.Boolean()

    _sql_constraints = [
        ('transsmart_nr_unique',
         'unique(transsmart_nr)',
         'Identifier field should be unique.')
    ]
