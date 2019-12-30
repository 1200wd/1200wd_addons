# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


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

    @api.multi
    def name_get(self):
        """Make code part of name."""
        result = []
        for this in self:
            name = super(DeliveryPackageType, this).name_get()[0][1]
            if not name:
                result.append((this.id, this.transsmart_code))
            else:
                result.append((this.id, " -  ".join([this.transsmart_code, name])))
        return result
