# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json

from transsmart.connection import Connection
from requests import HTTPError

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class TranssmartConfigSettings(models.TransientModel):
    _name = 'transsmart.config.settings'
    _inherit = 'res.config.settings'

    demo = fields.Boolean(default=True)
    username = fields.Char()
    password = fields.Char()
    account_code = fields.Char()

    @api.multi
    def get_default_transsmart(self):
        """Get default Transsmart from configuration parameters."""
        ir_config_parameter = self.env['ir.config_parameter']
        demo = ir_config_parameter.get_param('transsmart_demo')
        username = ir_config_parameter.get_param('transsmart_username')
        password = ir_config_parameter.get_param('transsmart_password')
        account_code = ir_config_parameter.get_param('transsmart_account_code')
        return {
            'demo': demo,
            'username': username,
            'password': password,
            'account_code': account_code,
        }

    @api.multi
    def set_transsmart_defaults(self):
        """Save the settings *and* synchronize the tables."""
        self.ensure_one()
        ir_config_parameter = self.env['ir.config_parameter']
        ir_config_parameter.set_param('transsmart_demo', self.demo)
        ir_config_parameter.set_param('transsmart_username', self.username)
        ir_config_parameter.set_param('transsmart_password', self.password)
        ir_config_parameter.set_param('transsmart_account_code', self.account_code,)
        try:
            self.synchronize_models()
        except HTTPError as exc:
            raise ValidationError(
                _("Error: %s" % (exc.response.json()['message'])))

    @api.multi
    def synchronize_models(self):
        """This will be invoked when the user saves the settings and by the cron job."""

        def get_connection():
            """Get transsmart connection."""
            return Connection().connect(
                settings['username'],
                settings['password'],
                settings['demo'],
            )

        def get_json_vals(json_object):
            """Get common values for Transsmart model from json object."""
            transsmart_nr = json_object['nr']
            json_value = json.loads(json_object['value'])
            vals = {
                'transsmart_nr': transsmart_nr,
                'transsmart_code': json_value['code'],
                'name': json_value.get('description', json_value.get('name')),
            }
            if 'isDefault' in json_value:
                vals['is_default'] = json_value['isDefault']
            return (json_value, vals)

        def create_or_write_transsmart(model, vals):
            """Use transsmart_nr to create or update model linked to transsmart."""
            record = model.search(
                [('transsmart_nr', '=', vals['transsmart_nr'])]
            )
            if not record:
                model.create(vals)
            else:
                record.write(vals)

        def get_cost_centers(connection):
            """Get Transsmart cost_centers."""
            response = connection.Account.retrieve_costcenter(settings['account_code'])
            model = self.env['transsmart.cost.center']
            for json_object in response.json():
                dummy_json_value, vals = get_json_vals(json_object)
                create_or_write_transsmart(model, vals)

        def get_service_level_others(connection):
            """Get Transsmart service level others."""
            response = connection.Account.retrieve_servicelevel_others(
                self.account_code)
            model = self.env['service.level.other']
            for json_object in response.json():
                dummy_json_value, vals = get_json_vals(json_object)
                create_or_write_transsmart(model, vals)

        def get_service_level_times(connection):
            """Get Transsmart service level time."""
            response = connection.Account.retrieve_servicelevel_time(self.account_code)
            model = self.env['service.level.time']
            for json_object in response.json():
                dummy_json_value, vals = get_json_vals(json_object)
                create_or_write_transsmart(model, vals)

        def get_delivery_package_types(connection):
            """Get Transsmart package types."""
            response = connection.Account.retrieve_packages(self.account_code)
            model = self.env['delivery.package.type']
            for json_object in response.json():
                json_value, vals = get_json_vals(json_object)
                vals.update({
                    'package_type': json_value['type'],
                    'length': json_value['length'],
                    'width': json_value['width'],
                    'height': json_value['height'],
                    'weight': json_value['weight'],
                })
                create_or_write_transsmart(model, vals)

        def get_default_package():
            """Get product that is the default package."""
            package_type_model = self.env['delivery.package.type']
            return package_type_model.search([('is_default', '=', True)], limit=1)

        def get_carriers(connection):
            """Get Transsmart carriers."""
            response = connection.Account.retrieve_carrier(self.account_code)
            model = self.env['res.partner']
            default_package = get_default_package()
            for json_object in response.json():
                json_value, vals = get_json_vals(json_object)
                vals.update({
                    'ref': vals['transsmart_code'],
                    'name': json_value['name'],
                    'carrier': True,
                    'customer': False,
                    'package_type_id': default_package.id,
                })
                create_or_write_transsmart(model, vals)

        def get_booking_profiles(connection):
            """Get Transsmart booking profiles."""
            response = connection.Account.retrieve_bookingprofiles(self.account_code)
            model = self.env['booking.profile']
            for json_object in response.json():
                json_value, vals = get_json_vals(json_object)
                profile_name = vals['name']
                carrier = get_transsmart_record(
                    'res.partner', json_value['carrier'], profile_name)
                service_level_time = get_transsmart_record(
                    'service.level.time', json_value['serviceLevelTime'],
                    profile_name)
                service_level_other = get_transsmart_record(
                    'service.level.other', json_value['serviceLevelOther'],
                    profile_name)
                incoterm = get_incoterm(json_value['incoterms'], profile_name)
                cost_center = get_transsmart_record(
                    'transsmart.cost.center', json_value['costCenter'],
                    profile_name)
                vals.update({
                    'carrier_id': carrier.id,
                    'service_level_time_id': service_level_time.id,
                    'service_level_other_id': service_level_other.id,
                    'incoterm_id': incoterm.id,
                    'cost_center_id': cost_center.id,
                    'mailtype': json_value['mailType'],
                })
                create_or_write_transsmart(model, vals)

        def get_transsmart_record(model_name, transsmart_code, profile_name):
            """Get transsmart record related to booking profile."""
            model = self.env[model_name]
            if not transsmart_code:
                return model.browse([])  # Empty recordset.
            record = model.search([('transsmart_code', '=', transsmart_code)], limit=1)
            if not record:
                raise ValidationError(
                    _('Code %s not found in model %s for booking profile %s.') %
                    (transsmart_code, model_name, profile_name)
                )
            return record

        def get_incoterm(incoterm_code, profile_name):
            """Get transsmart record related to booking profile."""
            incoterms_model = self.env['stock.incoterms']
            if not incoterm_code:
                return incoterms_model.browse([])  # Empty recordset.
            record = incoterms_model.search([('code', '=', incoterm_code)], limit=1)
            if not record:
                raise ValidationError(
                    _('Code %s not found in model %s for booking profile %s.') %
                    (incoterm_code, 'stock.incoterms', profile_name)
                )
            return record

        settings = self.get_default_transsmart()
        connection = get_connection()
        get_cost_centers(connection)
        get_service_level_others(connection)
        get_service_level_times(connection)
        get_delivery_package_types(connection)
        get_carriers(connection)
        get_booking_profiles(connection)
