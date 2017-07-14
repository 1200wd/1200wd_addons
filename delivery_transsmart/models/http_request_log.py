# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class HTTPRequestLog(models.Model):
    _name = 'http.request.log'
    _order = 'request_timestamp'

    request_timestamp = fields.Datetime(
        string='Date/time',
        default=fields.datetime.now(),
        required=True,
    )
    request_type = fields.String(
        string='Type',
        default='get',
        required=True,
    )
    request_url = fields.String(
        string='Url',
        required=True,
    )
    request_headers = fields.Text(
        string='Headers',
        required=True,
    )
    request_params = fields.Text(
        string='Params',
    )
    request_payload = fields.Text(
        string='Payload',
    )
    response_status_code = fields.Integer(
        string='HTTP response code',
        required=True,
    )
    response_data = fields.Text(
        string='Response data',
    )
