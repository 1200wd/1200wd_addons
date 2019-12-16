# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ResPartner(models.Model):
    """Delivery Carriers will be saved here."""
    _inherit = 'res.partner'

    transsmart_nr = fields.Integer('Identifier', index=True)
    transsmart_code = fields.Char()
    carrier = fields.Boolean()
    package_type_id = fields.Many2one(
        comodel_name='delivery.package.type',
        oldname='transsmart_package_type_id',
    )

    _sql_constrains = [
        ('transsmart_nr_unique',
         'unique(transsmart_nr)',
         'Identifier must be unique.')
    ]
