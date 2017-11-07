# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class DeliveryPackageType(models.Model):
    _name = 'delivery.package.type'
    _description = 'Package types accepted by Transsmart'

    name = fields.Char()
    package_type = fields.Char()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    weight = fields.Float()
    is_default = fields.Boolean()
    transsmart_id = fields.Integer()
