# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ProductTemplate(models.Model):
    """
    This model is used to hold the package types.
    https://devdocs.transsmart.com/#_packages_retrieval
    """
    _inherit = 'product.template'

    package = fields.Boolean()
    code = fields.Char()
    nr = fields.Integer('Identifier')
    description = fields.Char()
    _type = fields.Char()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    is_default = fields.Boolean()

    _sql_constraints = [
        ('nr_unique', 'unique(nr)', 'Identifier field should be unique.')]
