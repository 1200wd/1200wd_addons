# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 May
#    1200 Web Development
#    http://1200wd.com/
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


class AccountBankMatchConfiguration(models.Model):
    _name = 'account.config.settings'
    _inherit = 'account.config.settings'

    match_automatic_reconcile = fields.Boolean(
        "Reconcile found match automatically",
        help="When a match is found the bank statement line will automatically be reconciled with the match invoice",
    )

    match_cache_time = fields.Integer(
        "Match cache time in seconds", required=True,
        help="Store matches in cache and only recalculate if this number of seconds has passed. Enter -1 to disable caching.",
    )

    @api.model
    def get_default_bank_match_configuration(self, fields):
        ir_values_obj = self.env['ir.values']
        match_automatic_reconcile = ir_values_obj.get_default('account.bank.statement.match', 'match_automatic_reconcile') or False
        match_cache_time = ir_values_obj.get_default('account.bank.statement.match', 'match_cache_time') or 0
        return {
            'match_when_created': match_when_created,
            'match_automatic_reconcile': match_automatic_reconcile,
            'match_cache_time': match_cache_time,
        }

    @api.one
    def set_sale_bank_match_configuration(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.set_default('account.bank.statement.match', 'match_automatic_reconcile', self.match_automatic_reconcile)
        ir_values_obj.set_default('account.bank.statement.match', 'match_cache_time', self.match_cache_time)

    @api.one
    def action_generate_references(self):
        aj = self.env['account.journal'].search([('type', 'in', ['sale', 'sale_refund', 'purchase', 'purchase_refund'])])
        for journal in aj:
            seq = journal.sequence_id
            if (not seq.prefix and not seq.suffix):
                continue
            ref_pat = (seq.prefix or '') + '[0-9]{' + str(seq.padding) + '}' + (seq.suffix or '')
            if not self.env['account.bank.match.reference'].search_count([('name', '=', ref_pat)]):
                ref_seq = 10
                if 'refund' in journal.type: ref_seq += 5
                data = {
                    'name': ref_pat,
                    'model': 'account.invoice',
                    'sequence': ref_seq,
                    'score': 70,
                    'score_item': 20,
                    'company_id': journal.company_id.id,
                }
                _logger.debug("1200wd - Create match reference %s" % data)
                self.env['account.bank.match.reference'].create(data)