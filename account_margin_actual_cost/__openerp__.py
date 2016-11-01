# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Invoice - Actual Costs and Margins
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
    'name': "Account Invoice - Margins",
    'summary': """Use the actual product price to calculate margins on invoices""",
    'description': """
    * Depends on the sale_margin_actual_cost module
    """,
    'author': "1200 Web Development",
    'website': "http://www.1200wd.com",
    'category': 'Accounting & Finance',
    'version': '8.0.1.3',
    'depends': [
        'sale_margin_actual_cost',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/margin_reports.xml',
        'report/account_invoice_report_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 40.00,
    'currency': 'EUR',
}
