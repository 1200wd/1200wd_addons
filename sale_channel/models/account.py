# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales Channels
#    Copyright (C) 2016 June
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

from openerp import models, fields, api, _, exceptions


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _get_sales_channel_domain(self):
        ids = self.env.ref('res_partner_category.sales_channel').ids
        return [('category_id', 'in', ids)]

    sales_channel_id = fields.Many2one('res.partner', string="Sales channel",
                                       ondelete='set null', domain=_get_sales_channel_domain)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id, sales_channel_id)', 'Tax Name must be unique per company and sales channel!'),
    ]
