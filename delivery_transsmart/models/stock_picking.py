# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration
#    © 2016 - 1200 Web Development <http://1200wd.com/>
#    © 2015 - ONESTEiN BV (<http://www.onestein.nl>)
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
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning
import json
import logging

_logger = logging.getLogger(__name__)


def price_from_transsmart_price(price_str):
    """convert transsmart price string to odoo float field."""
    if price_str.startswith('EUR '):
        return float(price_str[4:].replace(',','.'))
    raise Warning(_("Couldn't convert transsmart price %s to float") % (price_str,))


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_service_level_time_id = fields.Many2one(
        'delivery.service.level.time',
        string='Delivery Service Level Time (PreBook)',
        ondelete="restrict")
    cost_center_id = fields.Many2one(
        'transsmart.cost.center',
        string='Delivery Cost Center')

    delivery_cost = fields.Float(
        'Delivery Cost',
        digits_compute=dp.get_precision('Product Price'),
        readonly=True)
    transsmart_id = fields.Integer(
        "Transsmart ID",
        readonly=True)
    transsmart_confirmed = fields.Boolean(
        "Transsmart Confirmed",
        compute="_compute_transsmart_confirmed",
        readonly=True,
        store=True)

    @api.depends('transsmart_id')
    def _compute_transsmart_confirmed(self):
        for rec in self:
            rec.transsmart_confirmed = bool(rec.transsmart_id)

    @api.multi
    def transsmart_cost_center_id(self):
        if self.cost_center_id and self.cost_center_id.transsmart_id:
            return self.cost_center_id.transsmart_id
        else:
            return None

    @api.multi
    def get_service_level_time_id(self):
        if self.carrier_id and self.carrier_id.product_id and self.carrier_id.product_id.service_level_time_id:
            return self.carrier_id.product_id.service_level_time_id.transsmart_id
        elif self.delivery_service_level_time_id.transsmart_id and not self.carrier_id:
            return self.delivery_service_level_time_id.transsmart_id
        else:
            return self.env['delivery.transsmart.config.settings'].transsmart_default_service_level_time_id()

    @api.multi
    def get_carrier_id(self):
        if self.carrier_id.partner_id.transsmart_id:
            carrier_id = self.carrier_id.partner_id.transsmart_id
        else:
            carrier_id = self.env['delivery.transsmart.config.settings'].transsmart_default_carrier_id()
        return carrier_id

    @api.multi
    def get_invoice_name(self):
        invoice_name = ''
        if self.sale_id.name:
            invoice_name = self.env['account.invoice'].search([('origin', '=', self.sale_id.name)]).number or ''
        return invoice_name

    def _transsmart_document_from_stock_picking(self):
        # TODO: Move to transsmart settings
        # HARDCODED weight correction: +3% +0.05kg , round to 1 decimal (=0.1kg)
        weight = float(round(((self.weight * 1.03) + 0.05), 1))

        document = {
            "Reference": filter(unicode.isalnum, self.name),
            "RefOrder": self.sale_id.name or '',
            "RefYourReference": self.sale_id.name or '',
            "RefOther": self.get_invoice_name(),
            "RefInvoice": self.get_invoice_name(),

            # take into account warehouse address, not just company address

            "AddressNamePickup": self.company_id.name or '',
            "AddressStreetPickup": self.company_id.street or '',
            "AddressStreet2Pickup": self.company_id.street2 or '',
            "AddressStreetNoPickup": ".",
            "AddressZipcodePickup": self.company_id.zip or '',
            "AddressCityPickup": self.company_id.city or '',
            "AddressStatePickup": self.company_id.state_id.code,
            "AddressCountryPickup": self.company_id.country_id.code or '',
            "AddressEmailPickup": self.company_id.email or '',
            "AddressPhonePickup": self.company_id.phone or '',

            "AddressName": self.partner_id.name or '',
            "AddressStreet": self.partner_id.street or '',
            "AddressStreet2": self.partner_id.street2 or '',
            "AddressStreetNo": ".",
            "AddressZipcode": self.partner_id.zip or '',
            "AddressCity": self.partner_id.city or '',
            "AddressState": self.partner_id.state_id.name or '',
            "AddressCountry": self.partner_id.country_id.code or '',
            "ColliInformation": [
                {
                    "PackagingType": "BOX",
                    "Description": "Description",
                    "Quantity": 1,
                    "Length": 8,
                    "Width": 10,
                    "Height": 30,
                    "Weight": weight,
                }
            ],

            "CarrierId": self.get_carrier_id(),
            "ServiceLevelTimeId": self.get_service_level_time_id(),
            "ShipmentValue": self.sale_id.amount_total,
            "ShipmentValueCurrency": "EUR",

            "AddressContact": self.partner_id.name or '',
            "AddressPhone": self.partner_id.phone or '',
            "AddressEmail": self.partner_id.email or '',
            "AddressCustomerNo": self.partner_id.ref or '',
        }

        if self.transsmart_cost_center_id():
            document.update({
                "CostCenterId": self.transsmart_cost_center_id()
            })

        if self.group_id:
            related_sale = self.env['sale.order'].search([('procurement_group_id','=',self.group_id.id)])

            if related_sale:
                document.update({
                    "AddressNameInvoice": related_sale.partner_invoice_id.name or '',
                    "AddressStreetInvoice": related_sale.partner_invoice_id.street or '',
                    "AddressStreet2Invoice": related_sale.partner_invoice_id.street2 or '',
                    "AddressStreetNoInvoice": ".",
                    "AddressZipcodeInvoice": related_sale.partner_invoice_id.zip or '',
                    "AddressCityInvoice": related_sale.partner_invoice_id.city or '',
                    "AddressStateInvoice": related_sale.partner_invoice_id.state_id.name or '',
                    "AddressCountryInvoice": related_sale.partner_invoice_id.country_id.code or '',
                })

        return document

    @api.one
    def action_get_transsmart_rate(self):
        if not self.company_id.transsmart_enabled or self.picking_type_id.code != 'outgoing':
            return
        # Exit if carrier is a not a Transsmart carrier
        if self.carrier_id.partner_id and not self.carrier_id.partner_id.transsmart_id:
            _logger.debug("1200wd - [{}] {} is not a Transsmart carrier. Skip prebooking.".
                          format(self.carrier_id.id, self.carrier_id.name))
            return

        document = self._transsmart_document_from_stock_picking()

        _logger.info("transsmart.getrates with document: %s" % (json.dumps(document),))
        r = self.env['delivery.transsmart.config.settings'].\
            get_transsmart_service().send('/Rates', params={'prebooking': 1, 'getrates': 0}, payload=document)
        if len(r):
            if type(r) == list:
                r = r[0]
        else:
            _logger.error("1200wd - Transsmart returned empty result: %s" % self.name)
            return
        _logger.info("transsmart.getrates returned: %s" % (json.dumps(r),))

        carrier = self.env['delivery.transsmart.config.settings'].lookup_transsmart_delivery_carrier(r)

        self.write({
            'carrier_id': carrier.id,
            'delivery_cost': price_from_transsmart_price(r['Price']),
        })

    @api.one
    def action_create_transsmart_document(self):
        if not self.company_id.transsmart_enabled or self.picking_type_id.code != 'outgoing':
            return
        # Exit if carrier is a not a Transsmart carrier
        if self.carrier_id.partner_id and not self.carrier_id.partner_id.transsmart_id:
            _logger.debug("1200wd - [{}] {} is not a Transsmart carrier. Skip create shipment.".
                          format(self.carrier_id.id, self.carrier_id.name))
            return

        if self.transsmart_id:
            raise Warning(_("This picking is already exported to Transsmart! : ") + self.name)

        document = self._transsmart_document_from_stock_picking()

        _logger.info("transsmart.document with document: %s" % (json.dumps(document),))
        r = self.env['delivery.transsmart.config.settings'].\
            get_transsmart_service().send('/Document', params={'autobook': 1}, payload=document)
        if len(r):
            if type(r) == list:
                r = r[0]
        else:
            _logger.error("1200wd - Transsmart returned empty result: %s" % self.name)
            return
        _logger.info("transsmart.document returned: %s" % (json.dumps(r),))

        carrier = self.env['delivery.transsmart.config.settings'].lookup_transsmart_delivery_carrier(r)
        data = {
            'transsmart_id': r['Id'],
            'carrier_id': carrier.id or '',
            'delivery_cost': r['ShipmentTariff'] or '',
            'carrier_tracking_ref': r['TrackingNumber'] or '',
            'carrier_tracking_url': r['TrackingUrl'] or '',
        }
        _logger.info("1200wd - Write Transsmart tracking data: {}".format(data))
        self.write(data)

    @api.multi
    def action_confirm(self):
        if self.env.context.get('ingoing_override', False):
            return super(StockPicking, self).action_confirm()
        self.action_get_transsmart_rate()
        return super(StockPicking, self).action_confirm()

    @api.model
    def create(self, vals):
        if 'action_ship_create' in self.env.context:
            vals.update({
                'cost_center_id': self.env.context['action_ship_create'].cost_center_id.id,
                'delivery_service_level_time_id':
                    self.env.context['action_ship_create'].delivery_service_level_time_id.id
            })
        r = super(StockPicking, self).create(vals)
        return r

    @api.multi
    def copy(self, default=None):
        context = context or {}
        default = default or {}
        default.update({
            'transsmart_confirmed': False,
            'transsmart_id': 0,
            'delivery_cost': 0
        })
        return super(StockPicking, self).copy(default=default)
