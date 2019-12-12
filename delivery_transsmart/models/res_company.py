# -*- coding: utf-8 -*-
# Copyright 2015-2017 1200wd  <https://www.1200wd.com>
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    transsmart_enabled = fields.Boolean('Use Transsmart')
