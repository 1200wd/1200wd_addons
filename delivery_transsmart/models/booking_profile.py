# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class BookingProfile(models.Model):
    _name = 'booking.profile'

    transsmart_nr = fields.Integer('Identifier', index=True)
    transsmart_code = fields.Char(index=True)
    name = fields.Char('Description')
    carrier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Carrier',
    )
    service_level_time_id = fields.Many2one(
        comodel_name='service.level.time',
        string='Service Level Time',
    )
    service_level_other_id = fields.Many2one(
        comodel_name='service.level.other',
        string='Service Level Other',
    )
    incoterm_id = fields.Many2one(
        comodel_name='stock.incoterms',
        string='Incoterms',
        oldname='incoterms_id',
    )
    cost_center_id = fields.Many2one(
        comodel_name='transsmart.cost.center',
        string='Costcenter',
    )
    mailtype = fields.Integer()
