# -*- coding: utf-8 -*-
##############################################################################
#
#    Bitcoin Integration Odoo
#    Copyright (C) 2017 July
#    1200 Web Development <http://1200wd.com/>
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
    'name': "Bitcoin",
    'summary': """Bitcoin and other Cryptocurrency integration in Odoo""",
    'description': """
Allows you to check incoming transactions on the blockchain and send payment requests
--- IN DEVELOPMENT ---
""",
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Accounting & Finance',
    'version': '9.0.1.4',
    'depends': [
        'account',
    ],
    'data': [
        'views/key.xml'
    ],
    'price': 0.00,
    'currency': 'EUR',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
