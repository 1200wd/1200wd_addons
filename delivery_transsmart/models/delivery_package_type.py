# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class DeliveryPackageType(models.Model):
    """This model is used to hold the package types."""
    _name = 'delivery.package.type'

    code = fields.Char(required=True, index=True)
    name = fields.Char()
    package_type = fields.Char(required=True)
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    weight = fields.Float()
    is_default = fields.Boolean()
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
            name = super(DeliveryPackageType, this).name_get()[0][1]
            if not name:
                result.append((this.id, this.code))
            else:
                result.append((this.id, " -  ".join([this.code, name])))
        return result

    @api.model
    def get_default(self):
        """Get (first) default package. In theory there should be only one."""
        return self.search(
            [('is_default', '=', True), ('active', '=', True)],
            limit=1
        )
