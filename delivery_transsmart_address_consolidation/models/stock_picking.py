# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration - Address Consolidation
#    Copyright (C) 2016 1200 Web Development (<http://1200wd.com/>)
#              (C) 2015 ONESTEiN BV (<http://www.onestein.nl>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _transsmart_create_shipping(self):
        document = super(StockPicking, self)._transsmart_create_shipping()
        document[0]['addresses'][1].update({
            "name": self.partner_id.name or '',
            "addressLine1": self.shipping_partner_street or '',
            "addressLine2": self.shipping_partner_street2 or '',
            "zipCode": self.shipping_partner_zip or '',
            "city": self.shipping_partner_city or '',
            "state": self.shipping_partner_state_id.name or '',
            "country": self.shipping_partner_country_id.code or '',
        })
        return document
