# -*- coding: utf-8 -*-
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=too-many-arguments,invalid-name,missing-docstring
import logging

from openerp import api, fields, models, registry


_logger = logging.getLogger(__name__)


class HTTPRequestLog(models.Model):
    _name = 'http.request.log'
    _order = 'request_timestamp desc'

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

    @api.model
    def append(self, response, payload=None):
        """Generic validation of Transsmart API response documents.

        Returns warnings and errors and takes care of logging.
        """
        log_cr = registry(self.env.cr.dbname).cursor()
        self = self.sudo().with_env(self.env(cr=log_cr))
        # use sudo() because it must always be possible to create a log
        request = response.request  # This is the prepared request.
        purged_headers = str({
            key: value for key, value in request.headers.items()
            if key != 'Authorization'
        }) if request.headers else False
        log_line = self.create({
            'request_timestamp': fields.datetime.now(),
            'request_type': request.method,
            'request_url': request.url,  # Contains also params.
            'request_headers': purged_headers,
            'request_payload': payload and str(payload) or False,
            'response_status_code': response.status_code,
            'response_data': response.text,
        })
        log_cr.commit()
        try:
            log_cr.close()
        except Exception:  # pylint: disable=broad-except
            _logger.warn("Could not close Transsmart request logging cursor.")
        if not log_line:
            _logger.warn("Could not create Transsmart Request log!")
