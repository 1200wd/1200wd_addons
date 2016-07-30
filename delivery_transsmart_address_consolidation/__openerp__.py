# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration - Address Consolidation
#    Copyright (C) 2016 1200 Web Development (<http://1200wd.com/>)
#              (C) 2015 ONESTEiN BV (<http://www.onestein.nl>)
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
    'name': "Transsmart Address Consolidation",
    'summary': """Address Consolidation support for Transsmart integration""",
    'description': """
    Integrates delivery_transsmart with address_consolidation
    Uses the denormalized address from address_consolidation in all
    stock_transsmart communication instead off the standard res_partner_address.

    This module is based on Onestein's version but is compatible with the new Transsmart API and has many bug fixes and improvements.
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Warehouse',
    'version': '8.0.2.0',
    'depends': [
        'delivery_transsmart',
        'address_consolidation'
    ],
    'data': [
    ],
    'demo': [],
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
