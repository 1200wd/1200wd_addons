# -*- coding: utf-8 -*-
# Copyright 2015-2017 1200wd <https://www.1200wd.com>
# Copyright 2017-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Transsmart Integration",
    'summary': """Transsmart Integration for Odoo""",
    'description': """
    Transsmart Integration for Odoo.
    Exchange delivery information between Odoo and Transsmart.
    """,
    'author': "1200 Web Development| Therp B.V",
    'category': 'Warehouse',
    'version': '8.0.3.3',
    'depends': [
        'delivery',
        'product_harmonized_system',
        'sale',
        'stock',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/transsmart_config_settings.xml",
        "views/res_company.xml",
        "views/sale_order.xml",
        "views/service_level_other.xml",
        "views/service_level_time.xml",
        "views/transsmart_cost_center.xml",
        "views/res_partner.xml",
        "views/stock_picking.xml",
        "views/delivery_package_type.xml",
        "views/booking_profile.xml",
        "wizards/stock_transfer_details.xml",
    ],
    'application': True,
    'external_dependencies': {
        'python': ['mock', 'transsmart']
    },
}
