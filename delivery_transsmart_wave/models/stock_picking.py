# -*- coding: utf-8 -*-
# Copyright 20182019 Therp BV <https://therp.nl>
# Copyright 2015-2016 1200 Web Development <https://1200wd.com>
# Copyright 2015 ONESTEiN BV <https://onestein.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_transsmart_book_shipping(self):
        document = super(StockPicking, self).action_transsmart_book_shipping()
        if self.wave_id.name and document:
            if document.get('additionalReferences'):
                document['additionalReferences'].append({
                    'type': 'YOUR_REFERENCE',
                    'value': self.wave_id.name,
                })
            else:
                document['additionalReferences'] = [{
                    'type': 'YOUR_REFERENCE',
                    'value': self.wave_id.name,
                }]
        return document
