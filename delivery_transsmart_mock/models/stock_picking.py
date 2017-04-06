# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import json

from openerp import models, api, _


_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def action_get_transsmart_rate(self):
        if not self.company_id.transsmart_enabled or \
                self.picking_type_id.code != 'outgoing':
            return
        # Exit if carrier is a not a Transsmart carrier
        if self.carrier_id.partner_id and \
                not self.carrier_id.partner_id.transsmart_id:
            _logger.debug(
                "1200wd - [{}] {} is not a Transsmart carrier."
                " Skip prebooking.".format(
                    self.carrier_id.id, self.carrier_id.name)
            )
            return
        document = self._transsmart_document_from_stock_picking()
        _logger.info(
            "Mock transsmart.getrates with document: %s" %
            (json.dumps(document),)
        )
        self.write({
            'carrier_id': self.carrier_id.id,
            'delivery_cost': 12.50,
        })

    @api.one
    def action_create_transsmart_document(self):
        if not self.company_id.transsmart_enabled or \
                self.picking_type_id.code != 'outgoing':
            return
        # Exit if carrier is a not a Transsmart carrier
        if self.carrier_id.partner_id and \
                not self.carrier_id.partner_id.transsmart_id:
            _logger.debug(
                "1200wd - [{}] {} is not a Transsmart carrier."
                " Skip create shipment.".format(
                    self.carrier_id.id, self.carrier_id.name)
            )
            return
        if self.transsmart_id:
            raise Warning(_(
                "This picking is already exported to Transsmart! : ") +
                self.name
            )
        document = self._transsmart_document_from_stock_picking()
        _logger.info(
            "Mock transsmart.document with document: %s" %
            (json.dumps(document),)
        )
        data = {
            'transsmart_id': '123',
            'carrier_id': str(self.carrier_id.id) or '',
            'delivery_cost': '16.70',
            'carrier_tracking_ref': 'Mock tracking ref',
            'carrier_tracking_url': 'Mock URL',
        }
        _logger.info(
            "1200wd - Write Transsmart tracking data: {}".format(data)
        )
        self.write(data)

    def get_tracking_transsmart(self, transsmart_id):
        """For the moment do actually nothing."""
        pass
