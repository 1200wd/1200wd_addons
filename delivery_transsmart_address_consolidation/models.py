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

from openerp import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    def _transsmart_document_from_stock_picking(self):
        """Use address consolidation fields for stock picking.
        """
        document = super(stock_picking, self)._transsmart_document_from_stock_picking()
        document.update({
            "AddressName": self.partner_id.name or '',
            "AddressStreet": self.shipping_partner_street or '',
            "AddressStreet2": self.shipping_partner_street2 or '',
            "AddressStreetNo": ".",
            "AddressZipcode": self.shipping_partner_zip or '',
            "AddressCity": self.shipping_partner_city or '',
            "AddressState": self.shipping_partner_state_id.name or '',
            "AddressCountry": self.shipping_partner_country_id.code or '',
        })

        if self.group_id:
            related_sale = self.env['sale.order'].search([('procurement_group_id','=',self.group_id.id)])
            if related_sale:
                document.update({
                    "AddressNameInvoice": related_sale.partner_invoice_id.name or '',
                    "AddressStreetInvoice": related_sale.invoice_partner_street or '',
                    "AddressStreet2Invoice": related_sale.invoice_partner_street2 or '',
                    "AddressStreetNoInvoice": "-",
                    "AddressZipcodeInvoice": related_sale.invoice_partner_zip or '',
                    "AddressCityInvoice": related_sale.invoice_partner_city or '',
                    "AddressStateInvoice": related_sale.shipping_partner_state_id.name or '',
                    "AddressCountryInvoice": related_sale.invoice_partner_country_id.code or '',
                })

        return document
