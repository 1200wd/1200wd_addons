# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "HTTP Request services",
    'summary': """Use HTTP Requests to communicatie with REST services.""",
    'description': """
    Exchange information with HTTP request services.
    """,
    'author': "Therp BV",
    'website': "https://therp.nl",
    'category': 'Tools',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/delivery_transsmart_views.xml",
        "views/service_level_views.xml",
        "views/res_config_views.xml",
        "views/delivery_web_service_views.xml",
        "views/http_request_log.xml",
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
