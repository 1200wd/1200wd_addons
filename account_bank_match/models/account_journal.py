# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.tools import safe_eval


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sales_channel_id = fields.Many2one(
        'res.partner',
        string='Sales Channel',
        domain=[('category_id.name', '=', 'Sales Channel')],
    )

    @api.model
    def _migrate_get_proper_channel(self):
        """
        Basically this sets the sales channel on the journals on group_1
        to Vaposhop, on group_2 to Conscious and everything else on Azarius.
        """
        group_1 = [
            'Tus. Rek. Pay.nl Shavita/ARI',
            'Tus.rek. Shavita/ARI',
            'Shavita Paypal',
            'Shavita Sofort',
            ]
        group_2 = ['Tus.rek. Conscious/ARI']
        res_partner = self.env['res.partner']
        vaposhop = res_partner.search([
            ('name', '=', 'Vaposhop'),
            ('category_id.name', '=', 'Sales Channel')],
            limit=1)
        self.search([
            ('name', 'in', group_1),
            ('sales_channel_id', '=', False)]).write({
                'sales_channel_id':  vaposhop.id})
        conscious = res_partner.search([
            ('name', '=', 'Conscious Wholesale'),
            ('category_id.name', '=', 'Sales Channel')],
            limit=1)
        self.search([
            ('name', 'in', group_2),
            ('sales_channel_id', '=', False)]).write({
                'sales_channel_id': conscious.id})
        azarius = res_partner.search([
            ('name', '=', 'Azarius'),
            ('category_id.name', '=', 'Sales Channel')],
            limit=1)
        self.search([
            ('name', 'not in', group_1 + group_2),
            ('sales_channel_id', '=', False)]).write({
                'sales_channel_id': azarius.id})

    @api.model
    def _migrate_add_sales_channel_on_rules(self):
        for match_rule in self.env['account.bank.match.rule'].search([
                ('model', 'in', ['sale.order', 'account.invoice'])]):
            t = safe_eval(match_rule.rule)
            t.append(
                ('sales_channel_id', '=', '@journal_id.sales_channel_id.id@'))
            match_rule.rule = str(t)
