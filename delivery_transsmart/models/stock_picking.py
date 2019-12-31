# -*- coding: utf-8 -*-
# Copyright 2016 1200 Web Development <https://1200wd.com/>
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,no-self-use,protected-access,invalid-name
from openerp import _, api, exceptions, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_service_level_time_id = fields.Many2one(
        comodel_name='delivery.service.level.time',
        string='Service Level Time',
    )
    cost_center_id = fields.Many2one(
        comodel_name='transsmart.cost.center',
        string='Delivery Cost Center',
    )
    service_level_other_id = fields.Many2one(
        comodel_name='delivery.service.level',
        string='Service Level Other',
    )
    transsmart_carrier_id = fields.Many2one(
        comodel_name='transsmart.carrier',
        string='Transsmart carrier',
    )
    incoterm_id = fields.Many2one(
        comodel_name='stock.incoterms',
        string='Incoterm',
    )
    package_type_id = fields.Many2one(
        comodel_name='delivery.package.type',
    )
    service = fields.Selection(
        [('DOCS', 'DOCS'), ('NON-DOCS', 'NON-DOCS')],
        default='NON-DOCS',
    )
    delivery_cost = fields.Float('Delivery Cost', readonly=True, copy=False)
    delivery_cost_currency_id = fields.Many2one('res.currency')

    @api.multi
    def action_transsmart_get_rates(self):
        """Get rates/offers from transsmart for the current picking.

        Attention: Only the lowest rate is saved.
        """
        service_model = self.env['delivery.web.service']
        service = service_model.get_current_service()
        for this in self:
            document = this.get_transsmart_rates_document()
            # document = this.get_transsmart_shipping_document()
            response = service.get_rates(document)[0]
            if 'rates' not in response:
                if 'errors' in response and \
                        'message' in response['errors']:
                    raise exceptions.ValidationError(
                        response['errors']['message']
                    )
                raise exceptions.ValidationError(str(response))
            this._update_rate_fields(response)

    @api.multi
    def _update_rate_fields(self, transsmart_response):
        """Update rate, but also selected carrier and service level time."""
        service_model = self.env['delivery.web.service']
        service = service_model.get_current_service()
        currency_model = self.env['res.currency']
        # Get lowest rate.
        rate_obj = sorted(transsmart_response['rates'], key=lambda x: x['price'])[0]
        price = rate_obj['price']
        currency = currency_model.search([('name', '=', rate_obj['currency'])])
        vals = {
            'delivery_cost': price,
            'delivery_cost_currency_id': currency.id,
        }
        vals['delivery_service_level_time_id'] = service.get_transsmart_record(
            self.env['delivery.service.level.time'],
            rate_obj['serviceLevelTime']
        ).id
        vals['service_level_other_id'] = service.get_transsmart_record(
            self.env['delivery.service.level'],
            rate_obj['serviceLevelOther']
        ).id
        vals['carrier_id'] = service.get_transsmart_record(
            self.env['transsmart.carrier'],
            rate_obj['carrier']
        ).id
        self.write(vals)

    def get_transsmart_rates_document(self):
        """Assemble and returns the payload to be sent to Transsmart to get rates."""
        self.ensure_one()
        document = {
            'reference': self.name,
            'description': self.name,
            'addresses': [
                self._get_address("SEND", self.company_id),
                self._get_address("RECV", self.partner_id),
            ],
            # for now a single package that contains everything
            'numberOfPackages': 1,
            'packages': [self._get_package()],
            'service': self.service,
            'serviceLevelTime': self.delivery_service_level_time_id.transsmart_code,
            'incoterms': self.incoterm_id.code or 'DAP',
            'costCenter': self.cost_center_id.transsmart_code,
            'pickupDate': fields.Datetime.from_string(self.min_date).date().isoformat(),
        }
        return document

    @api.multi
    def action_transsmart_book_shipping(self):
        """This creates the shipping on Transsmart."""
        service_model = self.env['delivery.web.service']
        service = service_model.get_current_service()
        for this in self:
            document = this.get_transsmart_shipping_document()
            response = service.create_shipping(document)[0]
            data = {
                'delivery_cost': response['price'],
                'carrier_tracking_ref': response['trackingUrl'],
            }
            this.write(data)

    def get_transsmart_shipping_document(self):
        """Assemble and returns the payload to be sent to Transsmart.

        See docs on: https://devdocs.transsmart.com/#_shipment_booking_only.
        """
        self.ensure_one()
        document = {
            'reference': self.name,
            'description': self.name,
            'additionalReferences': [
                {'type': 'ORDER', 'value': self.sale_id.name},
                {'type': 'OTHER', 'value': self._get_invoice_name()},
                {'type': 'INVOICE', 'value': self._get_invoice_name()},
            ],
            'addresses': [
                self._get_address("SEND", self.company_id),
                self._get_address("RECV", self.partner_id),
            ],
            # for now a single package that contains everything
            'numberOfPackages': 1,
            'packages': [self._get_package()],
            'value': self.sale_id.amount_total,
            'valueCurrency': self.sale_id.currency_id.name,
            'service': self.service,
            'serviceLevelTime': self.delivery_service_level_time_id.transsmart_code,
            'serviceLevelOther': self.service_level_other_id.transsmart_code,
            'incoterms': self.incoterm_id.code or 'DAP',
            'carrier': self.transsmart_carrier_id.transsmart_code,
            'costCenter': self.cost_center_id.transsmart_code,
            'pickupDate': fields.Datetime.from_string(self.min_date).date().isoformat(),
        }
        return document

    @api.multi
    def _get_invoice_name(self):
        if self.sale_id.name:
            invoice = self.env['account.invoice'].search(
                [('origin', '=', self.sale_id.name)],
                limit=1
            )
            if invoice:
                return invoice.number
        return ''

    def _get_address(self, address_type, record):
        """Get address from partner, company or other record with address fields."""
        return {
            'type': address_type,
            'name': record.name,
            'addressLine1': record.street,
            'addressLine2': record.street2,
            'zipCode': record.zip,
            'state': record.state_id.code,
            'city': record.city,
            'country': record.country_id.code,
            'email': record.email,
            'telNo': record.phone,
        }

    def _get_package(self):
        """Get package for shipment. For the moment hardcoded 1 package for all."""
        package = self.package_type_id
        return {
            'measurements':
                {
                    'length': package.length,
                    'width': package.width,
                    'height': package.height,
                    'weight': package.weight,
                    'linearUom': 'CM',
                    'massUom': 'KG',
                },
            'packageType': package.package_type,
            'quantity': 1,  # one package for everything
            'deliveryNoteInfo': {
                'deliveryNoteLines':
                    [self._get_delivery_line(line) for line in self.move_lines],
                }
            }

    def _get_delivery_line(self, line):
        """Get delivery line from stock move line."""
        return {
            'hsCode':
                line.product_id.hs_code_id.hs_code or
                line.product_id.category_hs_code_id.hs_code,
            'hsCodeDescription':
                line.product_id.hs_code_id.description or
                line.product_id.category_hs_code_id.description,
            'description': line.name,
            'price': line.product_id.lst_price,
            'currency': self.sale_id.currency_id.name,
            'quantity': line.product_uom_qty,
            'countryOrigin':
                line.product_id.origin_country_id.code,
            'articleId': self.product_id.default_code,
            'articleName': self.product_id.name,
            'articleEanCode': self.product_id.ean13,
            'reasonOfExport': self.reason_for_export,
        }
