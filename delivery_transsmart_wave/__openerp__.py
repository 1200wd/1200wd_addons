# -*- coding: utf-8 -*-
# Copyright 2018-2019 Therp BV <https://therp.nl>
# Copyright 2015-2016 1200 Web Development <https://1200wd.com>
# Copyright 2015 ONESTEiN BV <https://onestein.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Transsmart Wave",
    'summary': """Picking Wave support for Transsmart integration""",
    'description': """Send delivery orders to Transsmart using picking waves.""",
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Warehouse',
    'version': '8.0.3.0',
    'depends': [
        'delivery_transsmart',
        'stock_picking_wave'
    ],
    'data': [
        'views/stock_picking_wave.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
