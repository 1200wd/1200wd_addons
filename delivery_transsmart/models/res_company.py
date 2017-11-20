# -*- coding: utf-8 -*-
# © 2015-2017 1200wd  <http://www.1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    transsmart_enabled = fields.Boolean(
        'Use Transsmart',
        default=True,
    )
