# -*- coding: utf-8 -*-
##############################################################################
#
#    Product Price History View
#    Copyright (C) 2016 April
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
    'name': "Product Price History View",
    'summary': """View the purchase price history of products""",
    'description': """
        Odoo already keeps track of the history of purchase prices of products. With this simple module you are able to view these prices.
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Warehouse',
    'version': '9.0.1.1',
    'depends': [
        'product',
    ],
    'data': [
        'views/product_price_history_view.xml',
    ],
    'price': 10.00,
    'currency': 'EUR',
    'demo': [],
    'installable': False,
    'auto_install': False,
    'application': False,
}
