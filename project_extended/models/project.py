# -*- coding: utf-8 -*-
#
#    Project Extended
#    Copyright (C) 2015 November 
#    1200 WebDevelopment
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class project_project(models.Model):
    _inherit = "project.project"

    @api.multi
    def set_done(self):
        for project in self:
            if hasattr(project, 'task_ids'):
                for t in project.task_ids:
                    if not t.stage_id.fold:
                        raise Warning(
                            _("You can not close a project with open tasks. "
                              "Close or delete all task of this project first. (1)"))
            if hasattr(project, 'issue_ids'):
                for i in project.issue_ids:
                    if not i.stage_id.fold:
                        raise Warning(
                            _("You can not close a project with open issues. "
                              "Close or delete all issues of this project first. (2)"))

        return super(project_project, self).set_done()


class task(models.Model):
    _inherit = "project.task"

    stage_id = fields.Many2one(ondelete='restrict')

