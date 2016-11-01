# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales - Actual Costs and Margins
#    © 1200 WebDevelopment <http://1200wd.com/>
#    2016 November
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
    'name': "Sales Actual Costs and Margins",
    'summary': """Define extra costs per product to determine the actual price.
    The actual price is used to calculate margins on sale orders.
    """,
    'description': """
    * To calculate margins on Account Invoices also install the account_margin_actual_cost module.
    * This module is meant to replace the sale_margin module provided by Odoo S.A.
    """,
    'author': "1200 Web Development",
    'website': "http://www.1200wd.com",
    'category': 'Sales',
    'version': '8.0.1.3',
    'depends': [
        'product',
        'sale',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_cost_view.xml',
        'views/product_view.xml',
        'data/product.cost.type.csv',
        'views/sale_cost_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 50.00,
    'currency': 'EUR',
}
