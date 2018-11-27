# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase

from openerp.addons.account_bank_statement_import.parserlib import \
    BankTransaction


class TestStatementImport(TransactionCase):
    """Test methods used in bank statement import."""

    def test_empty_name(self):
        """Test move of name information to string."""
        import_model = self.env['account.bank.statement.import']
        transaction = BankTransaction()
        # Case 1, concat info from ref and name
        transaction['ref'] = 'ZZ12T32FYCIO7YPXC'
        transaction['name'] = 'virt AD 934637'
        import_model.empty_name(transaction)
        self.assertEqual(
            transaction['ref'], 'ZZ12T32FYCIO7YPXC virt AD 934637')
        self.assertEqual(transaction['name'], '/')
        # Case 2, info in ref already contained in name
        transaction['ref'] = 'ZZ12T32FYCIO7YPXC'
        transaction['name'] = 'virt ZZ12T32FYCIO7YPXC AD 934637'
        import_model.empty_name(transaction)
        self.assertEqual(
            transaction['ref'], 'virt ZZ12T32FYCIO7YPXC AD 934637')
        # Case 3, no ref at all
        transaction['ref'] = False
        transaction['name'] = 'virt AD 934637'
        import_model.empty_name(transaction)
        self.assertEqual(
            transaction['ref'], 'virt AD 934637')
