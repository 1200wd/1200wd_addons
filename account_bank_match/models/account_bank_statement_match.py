# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 April
#    1200 Web Development
#    http://1200wd.com/
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)

# TODO: Add constraints and indexes

# Object to store reference patterns of orders and invoices to look for in statement lines
class account_bank_statement_match_references(models.Model):
    _name = "account.bank.statement.match.reference"
    _order = "sequence,name"

    name = fields.Char(string="Reference Pattern", size=32,
                                    help="Regular expression pattern to match reference",
                                    required=True)
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
            ('account.account', 'Account'),
            ('res.partner', 'Partner'),
        ], select=True, required=True
    )
    sequence = fields.Integer('Sequence')
    account_bank_id = fields.Many2one('res.partner.bank', string='Bank Account',
        help='Match only applies to selected bank account. Leave empty to match all bank accounts.',
        domain="[('journal_id', '<>', False)]")
    score = fields.Integer("Score to Share", default=0, required=True, help="Total score to share among all matches of this rule. If 3 matches are found and the score to share is 30 then every match gets a score of 10.")
    score_item = fields.Integer("Score per Match", default=0, required=True, help="Score for each match. Will be added to the shared score.")
    account_account_id = fields.Many2one('account.account', string="Account")
    company_id = fields.Many2one('res.company', string='Company', required=True)

    _sql_constraints = [
        ('reference_pattern_name_company_unique', 'unique (name, model, company_id)', 'Use reference pattern only once for each model and for each Company')
    ]


# Object to store found matches to orders/invoices in statement lines
class account_bank_statement_match(models.Model):
    _name = "account.bank.statement.match"

    name = fields.Char(string="Reference", size=32, required=True,
                       help="Reference of match to order, invoice or account")
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
        ], select=True, required=True
    )
    statement_line_id = fields.Many2one('account.bank.statement.line', string="Bank Statement Line", required=True)
    description = fields.Char(string="Description", size=256)
    score = fields.Integer("Score")


# Object to store found matches to orders/invoices in statement lines
class account_bank_statement_match_rule(models.Model):
    """
    Example Rule:
    {   'name': "Sale Order amount match",
        'score_per_match': 100,
        'rule': "[('amount', '>', '@sale_order.amount-0.01@'), ('amount', '<', '@sale_order.amount-0.01@')]"
        'type': "sale.order"
    """
    _name = "account.bank.statement.match.rule"

    name = fields.Char(string="Title", size=256, required=True)
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
            ('account.move.line', 'Account Move'),
            ('res.partner', 'Partner'),
        ], select=True, required=True
    )
    score = fields.Integer("Score to Share", default=0, required=True, help="Total score to share among all matches of this rule. If 3 matches are found and the score to share is 30 then every match gets a score of 10.")
    score_item = fields.Integer("Score per Match", default=0, required=True, help="Score for each match. Will be added to the shared score.")
    active = fields.Boolean('Active', default=True, help='Set to inactive to disable rule')
    type = fields.Selection(
        [
            ('extraction', 'Extraction'),
            ('bonus', 'Bonus'),
        ], select=True, required=True, default='extraction')
    rule = fields.Text(string="Match Rule", required=True,
                       help="Rule to match a bank statement line to a sale order, invoice or account move. The rules should follow the Odoo style domain format.")
    script = fields.Text(string="Run Script",
                         help="Run Python code after rule matched. Be carefull what you enter here, wrong code could easily wreck your Odoo database")
    company_id = fields.Many2one('res.company', string='Company', required=False)


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    bank_statement_line_match_ids = fields.One2many('account.bank.statement.match', 'statement_line_id', "Matches")
