# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales Channels
#    Copyright (C) 2016 June
#    1200 Web Development
#    http://1200wd.com/
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

import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _get_sales_channel_domain(self):
        ids = []
        try:
            ids = self.env.ref('ari_sale.category_sales_channel').ids
        except ValueError:
            pass
        return [('category_id', 'in', ids)]

    sales_channel_id = fields.Many2one('res.partner', string="Sales channel", ondelete='set null',
                                       domain=_get_sales_channel_domain, required=False, index=True)

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False, company_id=False):
        _logger.debug('1200wd - account_invoice sale_channel onchange_partner_id')
        res = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False
        )
        partner = self.env['res.partner'].browse(partner_id)

        if partner_id:
            res['value'].update({
                'sales_channel_id': partner.sales_channel_id,
            })
        return res

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        _logger.debug('1200wd - account_invoice _prepare_refund include sales_channel')
        values = super(AccountInvoice, self)._prepare_refund(invoice, date=None, period_id=None, description=None,
                                                              journal_id=None)
        values.update({
            'sales_channel_id': invoice.sales_channel_id.id,
        })
        return values
