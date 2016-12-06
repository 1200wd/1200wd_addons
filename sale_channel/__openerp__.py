# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales Channels
#    © 2016 - 1200 WebDevelopment <http://1200wd.com/>
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
    'name': "Sale Channel",
    'summary': """Module to allow the use of multiple Sales Channels""",
    'description': """
    Allow the use of multiple sales channels for instance for different websites, countries and shops.

    For each sales channel you can specify a default pricelist, tax structure, address, sales person and many other
    settings.

    Easily filter sale orders, invoices and statistics by a specific sales channel.
    """,
    'author': "1200 Web Development",
    'website': "http://www.1200wd.com",
    'category': 'Sales',
    'version': '8.0.1.1.2',
    'depends': [
        'sale',
        'account',
    ],
    'data': [
        'data/res.partner.category.csv',
        'views/sale_view.xml',
        'views/partner_view.xml',
        'views/account_invoice_view.xml',
        'report/sale_report_view.xml',
        'report/invoice_report_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0.00,
    'currency': 'EUR',
}
