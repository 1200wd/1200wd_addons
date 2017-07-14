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
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Warehouse',
    'version': '8.0.3.1',
    'depends': [
        'delivery',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/delivery_transsmart_views.xml",
        "views/service_level_views.xml",
        "views/res_config_views.xml",
        "views/delivery_web_service_views.xml",
        "views/http_request_log.xml",
        "data/data.xml",
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
