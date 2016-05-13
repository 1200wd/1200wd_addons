# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 May
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

{
    'name': "Account Bank Match",
    'summary': """Match bank statement lines to sale orders or invoices""",
    'description': """
Match a bank statement line with an existing sales or purchase invoice or sale order. Based on extraction of
a Sale Order or Invoice reference, payment amount, bank account number, date or any other rule you can define yourself.

If one correct match is found automatically link and reconcile the statement line. If more matches are found you can select the best option from a list with probabilities.
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Accounting & Finance',
    'version': '8.0.1.1',
    'depends': [
        'account_bank_statement_advanced',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_view.xml',
        'views/account_bank_match.xml',
        'views/account_bank_statement_view.xml',
        'data/account.bank.match.rule.csv',
    ],
    'price': 200.00,
    'currency': 'EUR',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
