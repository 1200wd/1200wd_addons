# -*- coding: utf-8 -*-
#
#    Accounting Invoice Refund View
#    Copyright (C) 2016 February
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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    amount_untaxed_refund_view = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
                                              readonly=True, compute='_compute_amount', track_visibility='always')
    amount_total_refund_view = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                            readonly=True, compute='_compute_amount')
    residual_refund_view = fields.Float(string='Balance', digits=dp.get_precision('Account'),
                                        readonly=True, compute='_compute_residual')

    @api.one
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        if self.type in ('out_refund', 'in_refund'):
            self.amount_untaxed_refund_view = -self.amount_untaxed
            self.amount_total_refund_view = -self.amount_total
        else:
            self.amount_untaxed_refund_view = self.amount_untaxed
            self.amount_total_refund_view = self.amount_total

    @api.one
    def _compute_residual(self):
        super(AccountInvoice, self)._compute_residual()

        if self.type in ('out_refund', 'in_refund'):
            self.residual_refund_view = -self.residual
        else:
            self.residual_refund_view = self.residual