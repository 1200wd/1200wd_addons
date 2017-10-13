# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class TranssmartPackageType(models.Model):
    _name = 'transsmart.package.type'

    name = fields.Char()
    _type = fields.Char()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    weight = fields.Float()
    isDefault = fields.Boolean()
