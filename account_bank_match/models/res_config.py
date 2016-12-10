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
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class AccountBankMatchConfiguration(models.TransientModel):
    _inherit = 'account.config.settings'

    match_automatic_reconcile = fields.Boolean(
        "Reconcile found match automatically",
        help="When a match is found the bank statement line will automatically be reconciled with the match invoice",
    )
    match_cache_time = fields.Integer(
        "Match cache time in seconds", required=True,
        help="Store matches in cache and only recalculate if this number of seconds has passed. Enter -1 to disable caching.",
    )
    match_writeoff_journal_id = fields.Many2one('account.journal',
        string="Account journal to write of small differences", required=False,
        help="Small differences are automatically booked on this journal.",
    )
    match_writeoff_max_perc = fields.Float(string="% maximum difference writeoff", digits=dp.get_precision('Account'),
        help="Maximum percentage which will be write off automatically on specified journal")

    @api.model
    def get_default_bank_match_configuration(self, fields):
        ir_values_obj = self.env['ir.values']
        match_automatic_reconcile = ir_values_obj.get_default('account.bank.statement.match', 'match_automatic_reconcile') or False
        match_cache_time = ir_values_obj.get_default('account.bank.statement.match', 'match_cache_time') or 0
        match_writeoff_journal_id = ir_values_obj.get_default('account.bank.statement.match', 'match_writeoff_journal_id') or 0
        match_writeoff_max_perc = ir_values_obj.get_default('account.bank.statement.match', 'match_writeoff_max_perc') or 0.5
        return {
            'match_automatic_reconcile': match_automatic_reconcile,
            'match_cache_time': match_cache_time,
            'match_writeoff_journal_id': match_writeoff_journal_id,
            'match_writeoff_max_perc': match_writeoff_max_perc,
        }

    @api.one
    def set_sale_bank_match_configuration(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.set_default('account.bank.statement.match', 'match_automatic_reconcile', self.match_automatic_reconcile)
        ir_values_obj.set_default('account.bank.statement.match', 'match_cache_time', self.match_cache_time)
        ir_values_obj.set_default('account.bank.statement.match', 'match_writeoff_journal_id', self.match_writeoff_journal_id.id)
        ir_values_obj.set_default('account.bank.statement.match', 'match_writeoff_max_perc', self.match_writeoff_max_perc)

    @api.one
    def action_generate_references(self):
        aj = self.env['account.journal'].search([('type', 'in', ['sale', 'sale_refund', 'purchase', 'purchase_refund'])])
        for journal in aj:
            seq = journal.sequence_id
            if (not seq.prefix and not seq.suffix):
                continue
            ref_pat = (seq.prefix or '') + '[0-9]{' + str(seq.padding) + '}' + (seq.suffix or '')

            ref_obj = self.env['account.bank.match.reference'].search([('name', '=', ref_pat), ('company_id', '=', journal.company_id.id)])
            ref_seq = 10
            if 'refund' in journal.type: ref_seq += 5
            data = {
                'name': ref_pat,
                'model': 'account.invoice',
                'sequence': ref_seq,
                'score': 75,
                'score_item': 20,
                'company_id': journal.company_id.id,
            }
            if not len(ref_obj):
                _logger.debug("1200wd - Create match reference %s" % data)
                self.env['account.bank.match.reference'].create(data)
            elif len(ref_obj) == 1:
                _logger.debug("1200wd - Update match reference %s" % data)
                ref_obj.write(data)
            else:
                _logger.warning("1200wd - More then 1 match reference already exist: %s" % data)

