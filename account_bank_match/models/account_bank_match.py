# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 May
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

# TODO: Do not open old reconcile view when importing bank statements

from openerp.tools.translate import _
import logging

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError
import re
from datetime import date, timedelta

_logger = logging.getLogger(__name__)

# Object to store reference patterns of orders and invoices to look for in statement lines
class AccountBankMatchReference(models.Model):
    _name = "account.bank.match.reference"
    _order = "sequence,name"

    name = fields.Char(string="Reference Pattern", size=256,
                       help="Regular expression pattern to match reference")
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
            ('account.account', 'Account'),
            ('res.partner', 'Partner'),
        ], select=True, required=True
    )
    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active', default=True, help='Set to inactive to disable Match Reference')
    account_journal_id = fields.Many2one('account.journal', string='Journal Filter',
        help='Match only applies to selected journal. Leave empty to match all journals.', ondelete="cascade")
    score = fields.Integer("Score to Share", default=0, required=True, help="Total score to share among all matches of this rule. If 3 matches are found and the score to share is 30 then every match gets a score of 10.")
    score_item = fields.Integer("Score per Match", default=0, required=True, help="Score for each match. Will be added to the shared score.")
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete="cascade")
    account_account_id = fields.Many2one('account.account', string="Resulting Account", ondelete="cascade",
                                         domain="[('type', '=', 'other'), ('company_id', '=', company_id)]")
    partner_bank_account = fields.Char(string="Partner Bank Account", size=64, help="Remote owner bank account number to match")

    # FIXME: Disabled because it causes problems when matching with account_journal_id and empty names
    # _sql_constraints = [
    #     ('reference_pattern_name_company_unique', 'unique (name, model, company_id)', 'Use reference pattern only once for each model and for each Company')
    # ]

    @api.one
    @api.constrains('name')
    def _check_name_format(self):
        if self.name and re.search(r"\s", self.name):
            raise ValidationError('Please enter reference pattern without any whitespace character such as space or tab')

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _('%s_copy') % self.name
        return super(AccountBankMatchReference, self).copy(default)



class AccountBankMatchReferenceCreate(models.TransientModel):
    _name = "account.bank.match.reference.create"

    name = fields.Char(string="Reference Pattern", size=256,
                       help="Regular expression pattern to match reference. Leave emtpy to only match on Bank Account")
    partner_bank_account = fields.Char(string="Partner Bank Account", size=64, help="Remote owner bank account number to match")
    account_journal_id = fields.Many2one('account.journal', string='Journal Filter', ondelete="cascade",
        help='Match only applies to selected journal. Leave empty to match all journals.')
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete="cascade")
    account_account_id = fields.Many2one('account.account', string="Resulting Account", ondelete="cascade",
                                         domain="[('type', 'in', ['other','receivable','liquidity','payable']), ('company_id', '=', company_id)]")

    @api.multi
    def action_match_reference_save(self):
        data = {
            'name': self.name,
            'model': 'account.account',
            'sequence': 50,
            'account_journal_id': self.account_journal_id.id,
            'score_item': 100,
            'company_id': self.company_id.id,
            'account_account_id': self.account_account_id.id,
            'partner_bank_account': self.partner_bank_account,
        }
        self.env['account.bank.match.reference'].create(data)



# Object to store found matches to orders/invoices in statement lines
class AccountBankMatch(models.Model):
    _name = "account.bank.match"

    @api.model
    def _get_default_writeoff(self):
        configs = self.env['account.config.settings'].get_default_bank_match_configuration(self)
        return configs.get('match_writeoff_journal_id') or 0

    name = fields.Char(string="Reference", size=32, required=True,
                       help="Reference of match to order, invoice or account")
    so_ref = fields.Char('Sale Order Reference')
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
            ('account.account', 'Account'),
        ], select=True, required=True
    )
    statement_line_id = fields.Many2one('account.bank.statement.line', string="Bank Statement Line",
                                        required=True, index=True, ondelete="cascade")
    description = fields.Char(string="Description", size=256)
    score = fields.Integer("Score")
    writeoff_journal_id = fields.Many2one('account.journal', string="Write-off Journal", ondelete="cascade",
                                          default=_get_default_writeoff)
    writeoff_difference = fields.Boolean("Write-off Payment Difference", default=True)


    @api.multi
    def cron_cleanup_matches(self):
        try:
            datestr = (date.today() - timedelta(days=7)).__str__()
            # Using temporary table because DELETE ... WHERE is very slow on large tables
            # FIXME: Getting bad query warnings
            # self._cr.execute("CREATE TEMP TABLE account_bank_match_tmp AS "
            #                  "SELECT abm.* "
            #                  "FROM account_bank_match abm WHERE abm.create_date > %s", (datestr,))
            # self._cr.execute("ALTER TABLE account_bank_statement_line "
            #                  "DROP CONSTRAINT IF EXISTS account_bank_statement_line_match_selected_fkey")
            self._cr.execute("DELETE FROM account_bank_match WHERE create_date < %s", (datestr,))
            # self._cr.execute("ALTER TABLE account_bank_statement_line "
            #                  "ADD CONSTRAINT account_bank_statement_line_match_selected_fkey "
            #                  "FOREIGN KEY (match_selected) REFERENCES account_bank_match(id) ON DELETE SET NULL")
            # self._cr.execute("INSERT INTO account_bank_match SELECT * FROM account_bank_match_tmp")
            # self.invalidate_cache()
        except AttributeError:
            return False
        return True


    @api.one
    def compute_payment_difference(self):
        if self.model == 'account.invoice':
            SIGN = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
            invoice = self.env[self.model].search([('number', '=', self.name)])
            if not invoice:
                _logger.debug("1200wd - compute_payment_difference - invoice %s not found" % self.name)
                self.payment_difference = 0
            else:
                direction = SIGN[invoice.type]
                self.payment_difference = invoice.residual + (direction * self.statement_line_id.amount)
        else:
            # TODO: Add difference calculation for sale.order model
            self.payment_difference = 0

    payment_difference = fields.Float(string="Payment Difference", digits=dp.get_precision('Account'),
                                      readonly=True, compute='compute_payment_difference')


    @api.one
    def action_match_confirm(self):
        self.statement_line_id.show_errors = True
        vals = {'match_selected': self.id}
        if self.model == 'sale.order':
            vals['so_ref'] = self.name
            vals['name'] = '/'
        elif self.model == 'account.invoice':
            vals['name'] = self.name or '/'
        elif self.model == 'account.account':
            account_id = int(self.name) or 0
            self.statement_line_id.create_account_move(account_id)

        vals = self.statement_line_id.order_invoice_lookup(vals)
        self.statement_line_id.write(vals)
        if self.model != 'account.account':
            self.statement_line_id.auto_reconcile(type='manual')
        return True



# Object to store found matches to orders/invoices in statement lines
class AccountBankMatchRule(models.Model):
    """
    Example Rule:
    {   'name': "Sale Order amount match",
        'score_per_match': 100,
        'rule': "[('amount', '>', '@sale_order.amount-0.01@'), ('amount', '<', '@sale_order.amount-0.01@')]"
        'type': "sale.order"
    """
    _name = "account.bank.match.rule"

    name = fields.Char(string="Title", size=256, required=True)
    model = fields.Selection(
        [
            ('sale.order', 'Sale Order'),
            ('account.invoice', 'Invoice'),
            # ('account.move.line', 'Account Move'),
            ('res.partner', 'Partner'),
            ('account.bank.statement.line','Bank Statement Line'),
        ], select=True, required=True, help="Model used for search rule"
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
                         help="Run Python code after rule matched. Be carefull what you enter here, wrong code could damage your Odoo database")
    company_id = fields.Many2one('res.company', string='Company', ondelete="cascade", required=False)
