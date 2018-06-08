# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    © 2016 1200 Web Development <http://1200wd.com/>
#    © 2016 Therp BV <http://therp.nl>
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

from openerp import api, models


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
        stmt_vals = super(AccountBankStatementImport, self)._complete_statement(stmt_vals, journal_id, account_number)
        # set a custom statement name:
        if journal_id:
            sequence = self.env['account.journal'].browse(journal_id).sequence_id
            stmt_vals['name'] = sequence._next()
        # Update transactions:
        for transaction in stmt_vals['transactions']:
            if transaction.get('name') in ['NONREF', 'NOTPROVIDED']:
                transaction['name'] = ''
            if transaction.get('ref') in ['NONREF', 'NOTPROVIDED']:
                transaction['ref'] = ''
            transaction['name'] = '\n'.join(
                line
                for line in (transaction.get('name') or '').split('\n')
                if line not in [
                    'Referenz NOTPROVIDED',
                    'Verwendungszweck',
                ])
            self.empty_name(transaction)
            # Fill partner_name and counterparty_name:
            if transaction.get('partner_name'):
                transaction['counterparty_name'] = transaction['partner_name']
        return stmt_vals
