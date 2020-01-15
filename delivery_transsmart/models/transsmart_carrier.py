# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class TranssmartCarrier(models.Model):
    """This model is used to hold the carriers from Transsmart."""
    _name = 'transsmart.carrier'
    _description = "Transsmart Carrier"

    code = fields.Char(required=True, index=True)
    name = fields.Char()
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
            name = super(TranssmartCarrier, this).name_get()[0][1]
            if not name:
                result.append((this.id, this.code))
            else:
                result.append((this.id, " -  ".join([this.code, name])))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Search also on code."""
        args = args or []
        if name:
            # First search on code.
            records = self.search([('code', '=ilike', name + "%")] + args, limit=limit)
            if records:
                if limit and len(records) >= limit:
                    return records.name_get()
                # Get extra records if limit not reached.
                limit = limit if limit == 0 else limit - len(records)
                records = records | self.search(
                    [('name', operator, name)] + args, limit=limit)
                return records.name_get()
        #  If no code search, or nothing found, just call super.
        return super(TranssmartCarrier, self).name_search(
            name, args=args, operator=operator, limit=limit)
