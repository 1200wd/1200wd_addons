# -*- coding: utf-8 -*-
# © 2016 1200 WebDevelopment <1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Sale Channel",
    'summary': """Module to allow the use of multiple Sales Channels""",
    'description': """
    Allow the use of multiple sales channels for instance for different
    websites, countries and shops.

    For each sales channel you can specify a default pricelist, address,
    sales person and many other settings.

    Easily filter sale orders, invoices and statistics by a specific
    sales channel.
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
