# -*- coding: utf-8 -*-
# Copyright 2015 ONESTEiN BV <http://www.onestein.nl>
# Copyright 2016 1200 Web Development <https://1200wd.com/>
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_transsmart_book_shipping(self):
        document = super(StockPicking, self).action_transsmart_book_shipping()
        document['addresses'][1].update({
            "name": self.partner_id.name or '',
            "addressLine1": self.shipping_partner_street or '',
            "addressLine2": self.shipping_partner_street2 or '',
            "zipCode": self.shipping_partner_zip or '',
            "city": self.shipping_partner_city or '',
            "state": self.shipping_partner_state_id.name or '',
            "country": self.shipping_partner_country_id.code or '',
        })
        return document
