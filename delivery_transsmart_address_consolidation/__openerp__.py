# -*- coding: utf-8 -*-
# Copyright 2016 1200 Web Development <https://1200wd.com/>
# Copyright 2019-2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Transsmart Address Consolidation",
    'summary': """Address Consolidation support for Transsmart integration""",
    'description': """
    Integrates delivery_transsmart with address_consolidation.

    Uses the denormalized address from address_consolidation in all
    stock_transsmart communication instead off the standard
    res_partner_address.
    """,
    'author': "1200 Web Development",
    'website': "https://github.com/1200wd/1200wd_addons",
    'category': 'Warehouse',
    'version': '8.0.2.0',
    'depends': [
        'delivery_transsmart',
        'address_consolidation'
    ],
}
