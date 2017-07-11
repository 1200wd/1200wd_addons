# -*- coding: utf-8 -*-
##############################################################################
#
#    Accounting Invoice Tax Tests
#    Copyright (C) 2016 January
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
    'name': "Accounting Invoice Tax Tests",
    'summary': """Verify tax bookings of customer and supplier invoices""",
    'description': """
        Various extra tests will we added to the account_test module which check for differences
        in tax used on account invoices and tax booked in the account move lines.
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Accounting & Finance',
    'version': '9.0.1.0',
    'depends': [
        'account_test',
    ],
    'data': [
        'views/account_test_data.xml',
    ],
    'price': 10.00,
    'currency': 'EUR',
    'demo': [],
    'installable': False,
    'auto_install': False,
    'application': False,
}
