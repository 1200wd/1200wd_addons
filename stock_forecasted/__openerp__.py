# -*- coding: utf-8 -*-
##############################################################################
#
#    Stock Forecasted
#    1200 Web Development
#    http://1200wd.com/
#    Copyright (C) 2016 January
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
    'name': "Stock Forecast",
    'summary': """Stock forecast based on stock moves and sale orders""",
    'description': """

    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com/",
    'category': 'Warehouse',
    'version': '8.0.1.1',
    'depends': [
        'stock',
    ],
    'data': [
        'views/product_views.xml',
    ],
    'price': 100.00,
    'currency': 'EUR',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
