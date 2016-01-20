# -*- coding: utf-8 -*-
#
#    Project Group
#    Copyright (C) 2016 January
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

from openerp import models, fields


class ProjectGroup(models.Model):
	_name = 'project.group'
	_description = 'Project Group'
	_order = 'sequence'

	name = fields.Char(string='Name', size=50, required=True)
	description = fields.Text(string='Description', size=255)
	sequence = fields.Integer(string='Sequence')


class Project(models.Model):
	_inherit = 'project.project'
	_order = 'sequence'

	group_id = fields.Many2one('project.group', 'Project Group')

