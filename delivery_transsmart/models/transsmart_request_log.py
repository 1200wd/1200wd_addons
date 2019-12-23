# -*- coding: utf-8 -*-
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from openerp import api, fields, models, registry


_logger = logging.getLogger(__name__)


class TranssmartRequestLog(models.Model):
    _name = 'transsmart.request.log'
    _order = 'request_timestamp desc'

    request_timestamp = fields.Datetime(
        string='Date/time',
        required=True,
        readonly=True,
    )
    request_url = fields.Char(
        string='Url',
        required=True,
        readonly=True,
    )
    request_payload = fields.Text(
        string='Payload',
        readonly=True,
    )
    response_ok = fields.Boolean(
        string='Request succesfull',
        required=True,
        readonly=True,
    )
    response_data = fields.Text(
        string='Response data',
        readonly=True,
    )

    @api.model
    def append(self, request_url, document, response):
        """Generic validation of Transsmart API response documents.

        Returns warnings and errors and takes care of logging.
        """
        log_cr = registry(self.env.cr.dbname).cursor()
        self = self.sudo().with_env(self.env(cr=log_cr))
        # use sudo() because it must always be possible to create a log
        log_line = self.create({
            'request_timestamp': fields.datetime.now(),
            'request_url': request_url,
            'request_payload': str(document),
            'response_ok': response.ok,
            'response_data': response.text,
        })
        log_cr.commit()
        try:
            log_cr.close()
        except Exception:  # pylint: disable=broad-except
            _logger.warn("Could not close Transsmart request logging cursor.")
        if not log_line:
            _logger.warn("Could not create Transsmart Request log!")
