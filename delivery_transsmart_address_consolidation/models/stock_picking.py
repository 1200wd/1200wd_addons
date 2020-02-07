# -*- coding: utf-8 -*-
# Copyright 2019-2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_transsmart_document(self):
        """Use address fields from stock picking."""
        document = super(StockPicking, self).get_transsmart_document()
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
