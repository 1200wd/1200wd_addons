# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class DeliveryPackageType(models.Model):
    """
    This model is used to hold the package types.
    https://devdocs.transsmart.com/#_packages_retrieval
    """
    _name = 'delivery.package.type'

    transsmart_code = fields.Char(required=True, index=True)
    name = fields.Char()
    package_type = fields.Char(required=True)
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    weight = fields.Float()
    is_default = fields.Boolean()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('transsmart_code_unique',
         'unique(transsmart_code)',
         'Identifier field should be unique.')
    ]
