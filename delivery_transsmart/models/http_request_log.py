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
        readonly=True,
    )
    request_type = fields.Char(
        string='Type',
        default='get',
        required=True,
        readonly=True,
    )
    request_url = fields.Char(
        string='Url',
        required=True,
        readonly=True,
    )
    request_headers = fields.Text(
        string='Headers',
        required=True,
        readonly=True,
    )
    request_params = fields.Text(
        string='Params',
        readonly=True,
    )
    request_payload = fields.Text(
        string='Payload',
        readonly=True,
    )
    response_status_code = fields.Integer(
        string='HTTP response code',
        required=True,
        readonly=True,
    )
    response_data = fields.Text(
        string='Response data',
        readonly=True,
    )
