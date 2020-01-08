# -*- coding: utf-8 -*-
# Copyright 2016-2017 1200wd <https://www.1200wd.com>
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=too-many-arguments, missing-docstring, invalid-name, no-self-use
import getpass
import json
import logging
import requests

from requests.auth import HTTPBasicAuth

from openerp import _, api, exceptions, fields, models


_logger = logging.getLogger(__name__)


def clean_empty(in_object):
    """Remove recursively empty elements from nested dict/list object."""
    if not isinstance(in_object, (dict, list)):
        return in_object
    if isinstance(in_object, list):
        result_list = []
        for value in in_object:
            value = clean_empty(value)
            if value:
                result_list.append(value)
        return result_list
    # If we get here in_obejct must be a dictionary.
    result_dict = {}
    for key, value in in_object.items():
        value = clean_empty(value)
        if value:
            result_dict[key] = value
    return result_dict


def get_json_vals(json_object):
    """Get common values for Transsmart model from json object."""
    json_value = json.loads(json_object['value'])
    vals = {
        'code': json_value['code'],
        'name': json_value.get('description', json_value.get('name')),
    }
    if 'isDefault' in json_value:
        vals['is_default'] = json_value['isDefault']
    return (json_value, vals)


def validate_get_rates_document(document):
    """Check validity of document used to ask for a rate."""
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


def validate_create_booking_document(document):
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
                _("Field %s needs to have a value.") % field
            )
    for address in document.get('addresses'):
        for key in address.keys():
            if not address[key] and key not in ['addressLine2', 'state']:
                raise exceptions.ValidationError(
                    _("Field %s on address  needs to have a value.") % key
                )
    for package in document.get('packages'):
        for key in package.get('measurements').keys():
            if package.get('measurements')[key] is None:
                raise exceptions.ValidationError(_(
                    "Make sure that Package Type is set and its dimensions,"
                    " length, width, height and weight are filled."
                ))
        for field in REQUIRED_PACKAGE_FIELDS:
            if not package.get(field):
                raise exceptions.ValidationError(
                    _("Make sure that %s field of the Package Type has a value.") %
                    field
                )


class DeliveryWebService(models.Model):
    _name = 'delivery.web.service'

    instance_user = fields.Char(
        string="OS instance user",
        required=True,
        help="The os user onder which Odoo is running.\n"
             "This makes it easy to keep environments separate,"
             " even with copied databases.",
    )
    name = fields.Char(string="Title", required=True)
    url = fields.Char(
        string="URL",
        required=True,
        default="https://connect.test.api.transwise.eu/Api/"
    )
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    account = fields.Char(required=True)
    synchronization_time = fields.Datetime()

    _sql_constraints = [
        ('instance_user_unique',
         'unique(instance_user)',
         'Istance user field should be unique.')
    ]

    @api.model
    def get_current_service(self):
        """Get service according to the current os user."""
        instance_user = getpass.getuser()
        current = self.search([('instance_user', '=', instance_user)], limit=1)
        if not current:
            raise exceptions.ValidationError(
                _("No configuration defined for current os user %s.") % instance_user
            )
        return current

    @api.multi
    def post(self, endpoint, payload=None, **kwargs):
        self.ensure_one()
        request_headers = self._get_headers()
        response = requests.post(
            self.url + endpoint,
            json=payload,
            headers=request_headers,
            **kwargs
        )
        self._log_request_and_response(response, payload=payload)
        return self._return_response(response)

    @api.multi
    def get(self, endpoint, params=None, **kwargs):
        self.ensure_one()
        request_headers = self._get_headers()
        response = requests.get(
            self.url + endpoint,
            params=params,
            headers=request_headers,
            **kwargs
        )
        self._log_request_and_response(response)
        return self._return_response(response)

    @api.multi
    def action_check_connection(self):
        """Check connection by getting headers (does login)."""
        self.ensure_one()
        self._get_headers()

    @api.multi
    def action_synchronize(self):
        """Get configuration data from Transsmart."""
        self.ensure_one()
        self.synchronize_models()

    @api.multi
    def synchronize_models(self):
        """This will be invoked when the user saves the settings and by the cron job."""
        self.write({'synchronization_time': fields.Datetime.now()})
        self.get_service_level_times()
        self.get_service_level_others()
        self.get_delivery_package_types()
        self.get_cost_centers()
        self.get_carriers()

    def get_service_level_times(self):
        """Get Transsmart service level time."""
        model = self.env['delivery.service.level.time']
        endpoint = \
            "/v2/accounts/%s/listsettings/serviceLevelTimes" % self.account
        response = self.get(endpoint)
        for json_object in response:
            dummy_json_value, vals = get_json_vals(json_object)
            self.create_or_write_transsmart(model, vals)
        self.set_deprecated_inactive(model)

    def get_service_level_others(self, ):
        """Get Transsmart service level others."""
        model = self.env['delivery.service.level']
        endpoint = \
            "/v2/accounts/%s/listsettings/serviceLevelOthers" % self.account
        response = self.get(endpoint)
        for json_object in response:
            dummy_json_value, vals = get_json_vals(json_object)
            self.create_or_write_transsmart(model, vals)
        self.set_deprecated_inactive(model)

    def get_delivery_package_types(self, ):
        """Get Transsmart package types."""
        model = self.env['delivery.package.type']
        endpoint = \
            "/v2/accounts/%s/listsettings/packages" % self.account
        response = self.get(endpoint)
        for json_object in response:
            json_value, vals = get_json_vals(json_object)
            vals.update({
                'package_type': json_value['type'],
                'length': json_value['length'],
                'width': json_value['width'],
                'height': json_value['height'],
                'weight': json_value['weight'],
            })
            self.create_or_write_transsmart(model, vals)
        self.set_deprecated_inactive(model)

    def get_cost_centers(self, ):
        """Get Transsmart cost_centers."""
        model = self.env['transsmart.cost.center']
        endpoint = \
            "/v2/accounts/%s/listsettings/costCenters" % self.account
        response = self.get(endpoint)
        for json_object in response:
            dummy_json_value, vals = get_json_vals(json_object)
            self.create_or_write_transsmart(model, vals)
        self.set_deprecated_inactive(model)

    def get_carriers(self, ):
        """Get Transsmart carriers."""
        model = self.env['transsmart.carrier']
        endpoint = \
            "/v2/accounts/%s/listsettings/carriers" % self.account
        response = self.get(endpoint)
        for json_object in response:
            dummy_json_value, vals = get_json_vals(json_object)
            self.create_or_write_transsmart(model, vals)
        self.set_deprecated_inactive(model)

    @api.model
    def create_or_write_transsmart(self, model, vals):
        """Use transsmart code to create or update model linked to transsmart."""
        vals['active'] = True  # Reactivate if needed.
        record = self.get_transsmart_record(model, vals['code'])
        if not record:
            model.create(vals)
        else:
            vals.pop('code')  # Can not and should change.
            record.write(vals)

    @api.model
    def get_transsmart_record(self, model, code):
        """Return appropriate record if present, else an empty recordset."""
        return model.with_context(active_test=False).search(
            [('code', '=', code)]
        )

    @api.multi
    def set_deprecated_inactive(self, model):
        """Set records that were no longer present in synchronization inactive."""
        self.ensure_one()
        deprecated_records = model.search(
            [('write_date', '<', self.synchronization_time)]
        )
        deprecated_records.write({'active': False})

    @api.multi
    def get_rates(self, document):
        """Get rates for document from stock.picking."""
        self.ensure_one()
        document = clean_empty(document)
        validate_get_rates_document(document)
        endpoint = \
            "/v2/rates/%s" % self.account
        response = self.post(
            endpoint, payload=[document], params={'action': 'preBooking'}
            # endpoint, payload=[document]
        )
        return response

    @api.multi
    def create_shipping(self, document):
        """Create shipping for document from stock.picking."""
        self.ensure_one()
        document = clean_empty(document)
        validate_create_booking_document(document)
        endpoint = \
            "/v2/shipments/%s/BOOK" % self.account
        response = self.post(endpoint, payload=[document])
        return response

    @api.multi
    def _get_headers(self):
        """Get headers, including login token.

        TODO: Method can be enhanced to cache token, which is valid for 24 hours.
        """
        self.ensure_one()
        endpoint = '/login'
        response = requests.get(
            self.url + endpoint,
            auth=HTTPBasicAuth(self.username, self.password)
        )
        response.raise_for_status()
        token = 'Bearer ' + response.json()['token']
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
        }
        return headers

    def _log_request_and_response(self, response, payload=None):
        """Log request together with response."""
        log_model = self.env['http.request.log']
        log_model.append(response, payload=payload)

    def _return_response(self, response):
        """Generic handling of get and post requests.

        Returns warnings and errors and takes care of logging.
        """
        if response.status_code < 200 or response.status_code >= 300:
            _logger.error(
                "HTTP ERROR %s - %s",
                response.status_code,
                response.text
            )
            if "Message" in response.text:
                data = json.loads(response.text)
                error_message = data["Message"]
            else:
                error_message = \
                    "Transsmart communication error\n\n{}".format(response.text)
            raise exceptions.ValidationError(
                "ERROR {}: {}".format(response.status_code, error_message))
        return response.json()
