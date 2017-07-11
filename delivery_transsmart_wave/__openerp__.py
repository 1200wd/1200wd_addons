# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration - Picking Waves
#    Copyright (C) 2016 1200 Web Development (<http://1200wd.com/>)
#              (C) 2015 ONESTEiN BV (<http://www.onestein.nl>).
#              (C) 2015 1200 Web Development (<http://1200wd.com/>)
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
    'name': "Transsmart Wave",
    'summary': """Picking Wave support for Transsmart integration""",
    'description': """
This module allows the user to send delivvery orders to transsmart from using the Picking waves
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Warehouse',
    'version': '9.0.2.0',
    'depends': [
        'delivery_transsmart',
        'stock_picking_wave'
    ],
    'data': [
        'delivery_transsmart_wave_views.xml'
    ],
    'demo': [],
    'installable': False,
    'auto_install': False,
    'application': False,
}
