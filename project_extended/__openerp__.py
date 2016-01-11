# -*- coding: utf-8 -*-
##############################################################################
#
#    Project Extended
#    Copyright (C) 2015 November
#    1200 Web Development
#    http://1200wd.com/
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
    'name': "Project Extended",
    'summary': """Extensions for Project module""",
    'description': """
    Modification to improve the Odoo project module:
        * Add filter to hide Done, Cancelled and other folder stages
        * Prevents removal of projects with open tasks or issues
        * Prevents removal of project stages with tasks or issues
    """,
    'author': "1200 Web Development",
    'website': "http://1200wd.com",
    'category': 'Projects & Services',
    'version': '8.0.1.0',
    'depends': [
        'project',
        'project_issue',
    ],
    'data': [
        'views/project_view.xml',
        'views/project_issue_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
