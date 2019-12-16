# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class ServiceLevelOther(models.Model):
    """
    Used for keeping the Service Level Other records.
    https://devdocs.transsmart.com/#_service_level_other_retrieval
    """
    _name = 'service.level.other'

    transsmart_nr = fields.Integer('Identifier', required=True, index=True)
    transsmart_code = fields.Char(required=True, index=True)
    name = fields.Char()
    is_default = fields.Char()

    _sql_constraints = [
        ('transsmart_nr_unique',
         'unique(transsmart_nr)',
         'Identifier field should be unique.')
    ]
