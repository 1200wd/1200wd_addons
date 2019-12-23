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
        readonly=True,
    )
    service_level_other_id = fields.Many2one(
        comodel_name='delivery.service.level',
        string='Service Level Other',
        readonly=True,
    )
    transsmart_carrier_id = fields.Many2one(
        comodel_name='transsmart.carrier',
        string='Transsmart carrier',
        readonly=True,
    )
    incoterm_id = fields.Many2one(
        comodel_name='stock.incoterms',
        string='Incoterm',
        readonly=True,
    )
    package_type_id = fields.Many2one(
        comodel_name='delivery.package.type',
        readonly=True,
    )
    delivery_cost = fields.Float('Delivery Cost', readonly=True, copy=False)
    delivery_cost_currency_id = fields.Many2one('res.currency')
    service = fields.Selection(
        [('DOCS', 'DOCS'), ('NON-DOCS', 'NON-DOCS')],
        default='NON-DOCS',
    )

    @api.model
    def create(self, vals):
        """
        When a stock picking is created *and* can be sent to transsmart, get
        the rates.
        """
        result = super(StockPicking, self).create(vals)
        if self.company_id.transsmart_enabled \
                and self.picking_type_id.code == 'outgoing' \
                and self.booking_profile_id.carrier_id.transsmart_code:
            result.transsmart_get_rates()
        return result

    @api.multi
    def transsmart_get_rates(self):
        """
        Get rates/offers from transsmart for the current picking and set some
        values locally.
        Attention: Only the lowest rate is saved.
        https://devdocs.transsmart.com/#_calculating_rates
        """
        service_model = self.env['delivery.web.service']
        service = service_model.get_current_service()
        for rec in self:
            document = rec._transsmart_create_shipping()
            self._validate_get_rates_document(document)
            response = service.post('/get_rates', document)  # TODO: correct url
            response_json = response.json()[0]
            if 'rates' not in response_json:
                if 'errors' in response_json and \
                        'description' in response_json['errors']:
                    raise exceptions.ValidationError(
                        response_json['errors']['description']
                    )
                raise exceptions.ValidationError(response.text)
            # Get lowest rate.
            rate_obj = sorted(response_json['rates'], key=lambda x: x['price'])[0]
            rec.write({
                'delivery_cost': rate_obj['price'],
                'delivery_cost_currency_id': self.env['res.currency'].search(
                    [('name', '=', rate_obj['currency'])]).id
            })

    def _validate_get_rates_document(self, document):
        document = document[0]
        if not document.get('reference'):
            raise exceptions.ValidationError(_(
                "Reference field needs to be filled."))
        measurements = document.get('packages')[0].get('measurements')
        for key in measurements.keys():
            if not measurements[key]:
                raise exceptions.ValidationError(_(
                    "Make sure that the Package Type along with its fields "
                    "length, width, height and weight are set."))
        packageType = document.get('packages')[0].get('packageType')
        quantity = document.get('packages')[0].get('quantity')
        pickupDate = document.get('pickupDate')
        if not packageType or not quantity or not pickupDate:
            raise exceptions.ValidationError(_(
                "Package Type field on the Package Type must be filled. "
                "Sum of quantity of the product lines must not be zero. "
                "Pickup date must be filled."))
        for address in document.get('addresses'):
            for key in address.keys():
                if not address[key] and key != 'addressLine2':
                    raise exceptions.ValidationError(_(
                        "Field %s in the receiving and sending addresses must "
                        "be filled.") % (key))

    @api.multi
    def action_create_transsmart_document(self):
        """
        This creates the stock picking on Transsmart and sets some fields on
        the picking locally.
        https://devdocs.transsmart.com/#_shipment_booking_only
        """
        service_model = self.env['delivery.web.service']
        service = service_model.get_current_service()
        for rec in self:
            document = rec._transsmart_create_shipping()
            rec._validate_create_booking_document(document)
            response = service.post('/shipment_book', document)  # TODO: correct url
            response_json = response.json()[0]  # unpack
            data = {
                'delivery_cost': response_json['price'],
                'carrier_tracking_ref': response_json['trackingUrl'],
            }
            rec.write(data)

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

    def _transsmart_create_shipping(self):
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
            'packages': [self._get_package()],
            'carrier': self.booking_profile_id.carrier_id.transsmart_code,
            'value': self.sale_id.amount_total,
            'valueCurrency': self.sale_id.currency_id.name,
            'service': self.service,
            'serviceLevelTime': self.service_level_time_id.transsmart_code,
            'serviceLevelOther': self.service_level_other_id.transsmart_code,
            'incoterms': self.incoterm_id.code or 'DAP',
            'costCenter': self.cost_center_id.transsmart_code,
            'pickupDate': fields.Datetime.from_string(self.min_date).date().isoformat(),
        }
        return [document]

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

    def _validate_create_booking_document(self, document):
        document = document[0]
        REQUIRED_FIELDS = [
            'reference',
            'service',
            'serviceLevelTime',
            'pickupDate',
            ]
        REQUIRED_PACKAGE_FIELDS = [
            # 'packageType',
            'quantity',
            ]
        for field in REQUIRED_FIELDS:
            if not document.get(field):
                raise exceptions.ValidationError(
                    _("Field %s on %s needs to have a value.") % (field, self.name)
                )
        for address in document.get('addresses'):
            for key in address.keys():
                if not address[key] and key not in ['addressLine2', 'state']:
                    raise exceptions.ValidationError(
                        _("Field %s on address on %s needs to have a value.") %
                        (key, self.name))
        for package in document.get('packages'):
            for key in package.get('measurements').keys():
                if package.get('measurements')[key] is None:
                    raise exceptions.ValidationError(_(
                        "Make sure that Package Type is set on %s "
                        "or on the carrier "
                        "and its dimensions length, width, height and weight "
                        "are filled.") % (self.name))
            for field in REQUIRED_PACKAGE_FIELDS:
                if not package.get(field):
                    raise exceptions.ValidationError(
                        _("Make sure that %s field of the Package Type %s has a "
                          "value.") %
                        (field, self.package_type_id.name)
                    )
