# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################

{
    'name': "Accounting Invoice Refund View",
    'summary': """Show refund invoices correctly with negative amounts""",
    'description': """
        * Show Account Invoices of type Refund with a negative amount.
        * Fixes totals in account invoice overview, to match with outstanding partner balance.
        * Add Extra group by filter for invoice type (refund in/out, invoice in/out)
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Accounting & Finance',
    'version': '8.0.1.0',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice_view.xml',
    ],
    'price': 10.00,
    'currency': 'EUR',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
