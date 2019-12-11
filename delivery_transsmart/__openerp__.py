# -*- coding: utf-8 -*-
# © 2015-2017 1200wd  <http://www.1200wd.com>
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
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
        'stock',
        'delivery',
        'product_harmonized_system',
        'web_readonly_bypass',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/transsmart_config_settings.xml",
        "views/res_company.xml",
        "views/service_level_other.xml",
        "views/service_level_time.xml",
        "views/cost_center.xml",
        "views/res_partner.xml",
        "views/stock_picking.xml",
        "views/product_template.xml",
        "views/booking_profile.xml",
        "wizards/stock_transfer_details.xml",
    ],
    'application': True,
    'external_dependencies': {
        'python': ['mock', 'transsmart']
    },
}
