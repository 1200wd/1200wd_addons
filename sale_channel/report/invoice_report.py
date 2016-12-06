# -*- coding: utf-8 -*-
#
#    Sales Channels
#    © 2016 - 1200 WebDevelopment <http://1200wd.com/>
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

from openerp import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    sales_channel_id = fields.Many2one('res.partner', string="Sales channel", ondelete='set null', required=False)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """,
                    sub.sales_channel_id as sales_channel_id
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += """,
                    ai.sales_channel_id as sales_channel_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """,
                    ai.sales_channel_id
        """
        return group_by_str