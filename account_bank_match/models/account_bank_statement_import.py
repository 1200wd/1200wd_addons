# -*- coding: utf-8 -*-
# Copyright 2016 1200 Web Development <http://1200wd.com/>.
# Copyright 2016-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, models


NO_REFERENCE_VALUES = [
    'NONREF',
    'Referenz',
    'NOTPROVIDED',
    'NOT PROVIDED',
    'Verwendungszweck']

class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def empty_name(self, transaction):
        """Empty name, moving possible info to ref field."""
        ref = 'ref' in transaction and transaction['ref'] or ''
        name = 'name' in transaction and transaction['name'] or ''
        name = name != '/' and name or ''
        if ref in name or not ref:
            transaction['ref'] = name
        else:
            transaction['ref'] = ' '.join([ref, name])
        transaction['name'] = '/'

    @api.model
    def _complete_statement(self, stmt_vals, journal_id, account_number):
        """Override to set statement name from journal sequence.

        Also delete spurious info from ref in statement line, and complete
        statement line with partner_name and possibly so_ref
        (sales order reference).

        Also empty name field (that is, just use '/'), so this field will
        be available to fill in with invoice reference (this is copied more or
        less from existing code).
        """
        stmt_vals = super(
            AccountBankStatementImport, self
        )._complete_statement(stmt_vals, journal_id, account_number)
        # set a custom statement name:
        if journal_id:
            sequence = self.env['account.journal'].browse(
                journal_id).sequence_id
            stmt_vals['name'] = sequence._next()
        # Update transactions:
        for transaction in stmt_vals['transactions']:
            if transaction.get('name') in NO_REFERENCE_VALUES:
                transaction['name'] = ''
            if transaction.get('ref') in NO_REFERENCE_VALUES:
                transaction['ref'] = ''
            transaction['name'] = '\n'.join(
                line
                for line in (transaction.get('name') or '').split('\n')
                if line not in NO_REFERENCE_VALUES)
            self.empty_name(transaction)
            # Fill partner_name and counterparty_name:
            if transaction.get('partner_name'):
                transaction['counterparty_name'] = transaction['partner_name']
        return stmt_vals
