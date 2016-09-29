# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 May
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

from openerp import models, workflow, fields, api, _
from openerp.exceptions import Warning
import logging
import re
import ast
from datetime import datetime, timedelta
import pickle
import itertools

_logger = logging.getLogger(__name__)

# Match module settings, normally there should be no need to change them...
MATCH_MIN_SUCCESS_SCORE = 100
MATCH_MAX_PER_REFERENCE = 100


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self, cr, uid, ids=[], context=None):
        """ Override to skip the wizard and invoice the whole sales order"""
        if not context.get('override', False):
            return super(SaleAdvancePaymentInv, self).create_invoices(cr, uid, ids, context=context)
        res = []
        sale_obj = self.pool.get('sale.order')
        sale_ids = context.get('order_ids', [])
        if sale_ids:
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)['res_id'] or []
        return res



class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    so_ref = fields.Char('Sale Order Reference')
    name = fields.Char('Communication', required=True, default='/')

    match_ids = fields.One2many('account.bank.match', 'statement_line_id', "Matches", ondelete='set null')
    match_selected = fields.Many2one('account.bank.match', string="Winning Match", ondelete='set null')

    show_errors = False
    error_str = ""

    statement_text = ''


    def _handle_error(self, message):
        # global show_errors
        if self.show_errors:
            raise Warning(message)
        else:
            _logger.warning("1200wd - %s" % message)
            self.error_str += message + '/n'


    @api.model
    def _domain_reconciliation_proposition(self, st_line, excluded_ids=None):
        if excluded_ids is None:
            excluded_ids = []
        domain = ['|', ('ref', '=', st_line.name),
                       ('move_id.name', '=', st_line.name),
                  ('reconcile_id', '=', False),
                  ('state', '=', 'valid'),
                  ('account_id.reconcile', '=', True),
                  ('id', 'not in', excluded_ids)]
        return domain


    @api.model
    def prepare_bs_line(self, invoice, vals):
        if invoice.number:
            vals['name'] = invoice.number
        elif invoice.state == 'draft':
            invoice.signal_workflow('invoice_open')
            vals['name'] = invoice.number
        else:
            msg = "Could not create or validate invoice for sale order %s" % vals['so_ref']
            self._handle_error(msg)
        return vals


    @api.model
    def create_invoice(self):
        time_start = datetime.now()
        adv_inv_obj = self.env['sale.advance.payment.inv']
        inv_obj = self.env['account.invoice']
        # Create invoice
        self._context['override'] = True
        invoice_id = adv_inv_obj.create_invoices()
        invoice = inv_obj.browse(invoice_id)
        # Validate invoice
        invoice.signal_workflow('invoice_open')
        _logger.debug("1200wd - Created invoice in %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))
        return invoice


    @api.model
    def _prepare_create_invoice(self, order, vals):
        self._context.update({"order_ids": order.ids})
        invoice = self.create_invoice()
        # Add invoice reference to bank statement line
        time_start = datetime.now()
        ret = self.prepare_bs_line(invoice, vals)
        _logger.debug("1200wd - Prepare BS Line in %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))
        return ret


    @api.model
    def order_invoice_lookup(self, vals):
        """Find the invoice reference for the given order reference. Create an invoice if applicable."""
        if vals.get('so_ref', None):
            so_obj = self.env['sale.order']
            order = so_obj.search([('name', '=', vals['so_ref'])])
            if len(order) == 1:
                invoices = order.invoice_ids
                if len(invoices) == 1:
                    vals = self.prepare_bs_line(invoices[0], vals)
                elif len(invoices) > 1:
                    msg = "Expected 1 invoice, found %s invoices for orders: %s (ids)" % (len(invoices), vals['so_ref'])
                    self._handle_error(msg)
                else:
                    # Create invoice
                    if (order.order_policy == 'prepaid' or order.order_policy == 'manual') \
                            and order.state == 'wait_payment':
                        if order.signal_workflow('order_confirm'):
                            if order.order_policy == 'manual':
                                vals = self._prepare_create_invoice(order, vals)
                            elif order.order_policy == 'prepaid':
                                # Invoice has just been created and is still in draft, confirm it to lookup its name.
                                for invoice in order.invoice_ids:
                                    invoice.signal_workflow('invoice_open')
                                    vals['name'] = invoice.number
                    elif order.order_policy == 'manual' and order.state == 'manual':
                        vals = self._prepare_create_invoice(order, vals)
                    elif order.order_policy == 'prepaid' and order.state != 'wait_payment':
                        msg = "Trying to pay for Sale Order {} when its state is not 'Wait for Payment'.".format(vals['so_ref'])
                        self._handle_error(msg)
                    else:
                        msg = "Create invoice skipped, order policy and state are {} and {} resp.".format(order.order_policy, order.state)
                        self._handle_error(msg)
            else:
                msg = "One sale order expected. Found %s sale orders for reference: %s" % (len(order), vals['so_ref'])
                self._handle_error(msg)
        return vals


    @api.model
    def _extract_references(self):
        """
        Extract references defined in the 'account.bank.match.reference' table
        from account bank statement line.

        @return: matches
        Format {name, [sale order reference], model, [description], score total, score per item}
        """
        try:
            remote_account = ''
            if self.partner_id:
                partner_bank = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id)])
                if partner_bank and 'sanitized_acc_number' in partner_bank:
                    remote_account = partner_bank.sanitized_acc_number
            statement_text = (self.name or '') + '_' + (self.partner_id.name or '') + '_' + (self.ref or '') + '_' + (self.so_ref or '') + '_' + remote_account
        except Exception, e:
            msg = "Could not parse statement text for %s" % self.name
            self._handle_error(msg)
            return []
        statement_text = re.sub(r"\s", "", statement_text).upper()
        self.statement_text = statement_text
        company_id = self.env.user.company_id.id
        matches = []
        count = 0

        search_domain = ['|', ('company_id', '=', False), ('company_id', '=', company_id),
                         '|', ('account_journal_id', '=', False), ('account_journal_id', '=',
                                                                   self.journal_id.id or self.statement_id.journal_id.id),
                         '|', ('partner_bank_account', '=', False), ('partner_bank_account', '=', remote_account)]
        match_refs = self.env['account.bank.match.reference'].search(search_domain)
        for match_ref in match_refs:
            try:
                if not match_ref.name:
                    name = '/'
                    if match_ref.account_account_id:
                        name = match_ref.account_account_id.id
                    obj = self.env[match_ref.model].search([(self._match_get_field_name(match_ref.model), '=', name)])
                    description = "%s; Partner bank %s" % (self._match_description(obj, match_ref.model), match_ref.partner_bank_account)
                    matches.append(
                        {'name': name,
                         'so_ref': '',
                         'model': match_ref.model,
                         'description': description,
                         'score': match_ref.score,
                         'score_item': match_ref.score_item,
                         })
                    continue
                for m in re.finditer(match_ref.name, statement_text):
                    name = m.group(0)
                    if match_ref.account_account_id:
                        name = match_ref.account_account_id.id
                    obj = self.env[match_ref.model].search([(self._match_get_field_name(match_ref.model), '=', name)])
                    description = self._match_description(obj, match_ref.model)
                    if match_ref.model == 'account.invoice': so_ref = obj.origin or ''
                    elif match_ref.model == 'sale.order': so_ref = name
                    else: so_ref = ''
                    matches.append(
                        {'name': name,
                         'so_ref': so_ref,
                         'model': match_ref.model,
                         'description': description,
                         'score': match_ref.score,
                         'score_item': match_ref.score_item,
                         })
                    count += 1
                    if count > MATCH_MAX_PER_REFERENCE: break
            except Exception, e:
                msg = "Please check Bank Match Reference patterns an error occured while parsing '%s'. Error: %s" % (match_ref.name, e.args[0])
                self._handle_error(msg)
        return matches


    @api.model
    def _parse_rule(self, rule):
        """
        Convert rule from account.bank.match.rule to Odoo format

        @param rule: record from account.bank.match.rule
        @return: Odoo styled rule
        """
        rule_list = []
        try:
            rule_list = ast.literal_eval(rule.rule)
        except Exception, e:
            msg = "Could not parse rule '{}'. Error Message: {}".format(rule.rule, e.message)
            self._handle_error(msg)
            return False

        rule_list_new = []
        for field_name, operator, value in rule_list:
            new_value = None
            if isinstance(value, str):
                matches = re.search("@(.+?)@", value)
                if matches:
                    found_odoo_expression = matches.group(1)
                    if found_odoo_expression == 'None':
                        new_value = None
                    elif 'today' in found_odoo_expression:
                        numofdays = int(re.search("today-(\d+)", found_odoo_expression).group(1))
                        new_value = ((datetime.now() - timedelta(days=numofdays)).strftime('%Y-%m-%d'))
                    elif 'days' in found_odoo_expression:
                        try:
                            rs = re.search("(.+?)([\-|\+])days\((\d+)\)", found_odoo_expression)
                            field = rs.group(1)
                            sign = rs.group(2)
                            numofdays = int(rs.group(3))
                            field_value = eval("self." + field)
                            ndate = datetime.strptime(field_value,'%Y-%m-%d')
                            if sign=='-':
                                 ndate -= timedelta(days=numofdays)
                            else:
                                ndate += timedelta(days=numofdays)
                            new_value = ndate.strftime('%Y-%m-%d')
                        except Exception, e:
                            msg = "Rule '%s'. Error matching odoo expression '%s' %s" % (rule.rule, found_odoo_expression, e.message)
                            self._handle_error(msg)
                            return False
                    else:
                        odoo_expression = re.sub("@(.+?)@", "self." + found_odoo_expression, value)
                        try:
                            # !!!Please note!!!: This executes the string as python code, set security rules wisely!
                            new_value = eval(odoo_expression)
                            if not new_value:
                                rule_list_new.append(('id', '=', False))  # Always False
                                continue
                        except Exception, e:
                            msg = "Rule '%s'. Error matching odoo expression '%s' %s" % (rule.rule, odoo_expression, e.message)
                            self._handle_error(msg)
                            return False
            if new_value:
                rule_list_new.append((field_name, operator, new_value))
            else:
                rule_list_new.append((field_name, operator, value))

        return rule_list_new


    @api.model
    def _update_match_list(self, match, add_score, matches=[]):
        """
        Add a new match to the match list

        @param match: New match
        @param add_score: New score
        @param matches: Match list
        @return: Updated match list
        """
        if not 'so_ref' in match:
            msg ="_update_match_list: Missing so_ref in match"
            self._handle_error(msg)
            return matches

        # If match is an account move line ...
        # if match['model'] == 'account.move.line':
            # aml = self._match_get_object('account.move.line', match['name'])

        # If match is a partner replace match with open invoices of this partner
        elif match['model'] == 'res.partner':
            partner = self._match_get_object('res.partner', match['name'])
            open_invoices = [i for i in partner.invoice_ids if i.state == 'open']
            for invoice in open_invoices:
                description = self._match_description(invoice, 'account.invoice')
                sc = add_score / len(open_invoices)
                matches = self._update_match_list({'name': invoice.number, 'model': 'account.invoice',
                                                   'description': description, 'so_ref': invoice.origin or ''}, sc, matches)
            open_orders = [o for o in partner.sale_order_ids if o.state in ['draft', 'wait_payment', 'sent']]
            for order in open_orders:
                description = self._match_description(order, 'sale.order')
                sc = add_score / len(open_orders)
                matches = self._update_match_list({'name': order.name, 'model': 'sale.order',
                                                   'description': description, 'so_ref': order.name}, sc, matches)
            return matches

        # If match to a sale order and sale order has an invoice then replace match with invoice number
        elif match['model'] == 'sale.order':
            invoice = self._match_get_object('sale.order', match['name']).invoice_ids
            # TODO: Handle situation where 1 sale order has multiple invoices or other n-m relations
            if len(invoice) == 1:
                match['description'] += ";" + match['name']
                match['model'] = 'account.invoice'
                match['so_ref'] = match['name']
                match['name'] = invoice.number or ''

        # Remove duplicates and sum up scores
        if match['name'] not in [d['name'] for d in matches]:
            matches.append(
                {'name': match['name'],
                 'model': match['model'],
                 'score': add_score,
                 'description': match.get('description', ''),
                 'so_ref': match.get('so_ref', ''),})
        else:
            # Adapt score for subsequent matches to avoid extreme high scores
            score_current = [d['score'] for d in matches if d['name']==match['name']][0]
            weight_factor = 1.0 / max(1.0, max(score_current-50,1)/25.0)
            add_score = int(add_score * weight_factor)
            [
                d.update(
                    {'score': d['score'] + add_score,
                     'so_ref': d['so_ref'] or '',
                     'description': d['description']})
                for d in matches if d['name'] == match['name']
            ]

        return matches


    @api.model
    def _match_description(self, object, model):
        """
        Generate description of match
        @param object: match object
        @param model: match type (invoice, sale order, account move)
        @return: description
        """
        description = ''
        try:
            currency_symbol = ''
            if 'currency_id' in object:
                currency_symbol = object.currency_id.name or ''
            if model == 'account.invoice':
                description = (object.number or 'Not found') + "; " + (object.origin or '') + "; " + (object.supplier_invoice_number or '') + "; " + (object.date_invoice or '') + "; " + (object.partner_id.name or '') + "; " + \
                              (object.state or '') + "; " + currency_symbol + " " + str(object.amount_total or '')
            # elif model == 'account.move.line':
            #     description = (object.ref or 'Not found') + "; " + (object.date or '') + "; " + (object.partner_id.name or '') + "; " + \
            #                   (object.state or '') + "; " + currency_symbol + " " + str(object.debit or '')
            elif model == 'sale.order':
                description = (object.date_order or 'Not found') + "; " + (object.partner_id.name or '') + "; " + \
                              (object.state or '') + "; " + currency_symbol + " " + str(object.amount_total)
            elif model == 'account.account':
                description = "Book full amount on account %s - %s" % (object.code, object.name)
            while "; ;" in description:
                description = description.replace("; ;",";")

        except Exception, e:
            msg = "Could not construct match description. Error %s" % e.args[0]
            self._handle_error(msg)
        return description


    @api.model
    def _match_get_name(self, object, model):
        if model == 'account.invoice':
            return object.number
        elif model == 'sale.order':
            return object.name
        else:
            return str(object.id)


    @api.model
    def _match_get_field_name(self, model):
        if model == 'account.invoice':
            return 'number'
        elif model == 'sale.order':
            return 'name'
        else:
            return 'id'


    @api.model
    def _match_get_datefield_name(self, model):
        if model == 'account.invoice':
            return 'date_invoice'
        # elif model == 'account.move.line':
        #     return 'date'
        elif model == 'sale.order':
            return 'date_order'
        else: return ''


    @api.model
    def _match_get_base_domain(self, model):
        """
        Base domain when searching matches for given model

        @param model: type of model
        @return: base domain
        """
        daysback = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        company_id = self.env.user.company_id.id
        domain = ['|', ('company_id', '=', False), ('company_id', '=', company_id)]
        if model == 'sale.order':
            domain.extend([('date_order', '>', daysback),
                           ('state', 'in', ['draft', 'wait_payment', 'sent'])])
        elif model == 'account.invoice':
            domain.extend([('date_invoice', '>', daysback),
                           ('state', 'in', ['open'])])
        # elif model == 'account.move.line':
        #     domain.extend([('date', '>', daysback), ('reconcile_ref', '=', False)])

        return domain


    @api.model
    def _match_get_object(self, model, ref, domain = None):
        if domain is None:
            domain = []
        # else:
        #     import pdb; pdb.set_trace()
        try:

            m = self.env[model]
            if model == 'account.invoice':
                # return m.search(['|', ('number', '=', ref), ('reference', '=', ref)] + domain, limit=1)
                return m.search([('number', '=', ref)] + domain, limit=1)
            elif model == 'sale.order':
                return m.search([('name', '=', ref)] + domain, limit=1)
            else:
                return m.search([('id', '=', ref)] + domain, limit=1)

        except Exception, e:
            msg = "Could not open model %s with reference %s. Error %s" % (model, ref, e.args[0])
            self._handle_error(msg)
        return False


    @api.model
    def match_search(self):
        """
        Search all matches with invoices, sale order of account move for this bank statement line.

        - Extract matches with reference patterns defined in account.bank.match.reference and add them to the match list
        - Run all extraction rules defined in account.bank.match.rules and add new matches to the match list
        - Run all bonus rules and updates scores

        @return: Sorted list of matches with higher score first
        """
        time_start = datetime.now()
        # Delete old match records
        try:
            self._cr.execute("DELETE FROM account_bank_match WHERE statement_line_id=%d" % self.id)
            self.invalidate_cache()
        except AttributeError:
            return False
        _logger.debug("1200wd - Search matches - delete old %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        # Search matches with reference pattern
        time_start = datetime.now()
        company_id = self.env.user.company_id.id
        matches = []
        ref_matches = self._extract_references()
        if ref_matches:
            base_score = sum([d['score'] for d in ref_matches]) / len(ref_matches)
            for ref_match in ref_matches:
                matches = self._update_match_list(ref_match, base_score + ref_match['score_item'], matches)
        _logger.debug("1200wd - Search matches - ref patterns - %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        # Search supplier reference in bank statement line
        time_start = datetime.now()
        ref_matches = []
        supplier_inv_list = self.env['account.invoice'].search_read([
            ('supplier_invoice_number', '!=', False),
            ('state', '=', 'open')],['number', 'supplier_invoice_number'])
        for supplier_inv in supplier_inv_list:
            supplier_ref = supplier_inv['supplier_invoice_number']
            if len(supplier_ref)<3: continue
            if supplier_ref in self.statement_text:
                inv_number = supplier_inv['number']
                obj = self.env['account.invoice'].search([('number', '=',inv_number)])
                description = self._match_description(obj, 'account.invoice')
                # Add bonus, increase score depending on number of characters of supplier reference
                score = 40 + min(50,(len(supplier_ref)-3)*10)
                ref_matches.append(
                    {'name': inv_number, 'so_ref': '', 'model': 'account.invoice', 'description': description, 'score': 0, 'score_item': score,})
        if ref_matches:
            for ref_match in ref_matches:
                matches = self._update_match_list(ref_match, ref_match['score_item'], matches)
        _logger.debug("1200wd - Search matches - search ref - %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        # Run match rules on invoices, sale orders
        time_start = datetime.now()
        for rule in self.env['account.bank.match.rule'].search(
                ['|', ('company_id', '=', False), ('company_id', '=', company_id),
                ('type', '=', 'extraction')]):
            rule_domain = self._parse_rule(rule)
            if not rule_domain: # stop running rule if empty domain is returned to avoid useless matches on rule parsing errors
                continue
            base_domain = self._match_get_base_domain(rule['model'])
            orderby_field = self._match_get_datefield_name(rule['model'])
            if orderby_field: orderby_field += ' DESC'
            rule_matches = self.env[rule['model']].search(base_domain + rule_domain, limit=15, order=orderby_field)
            if rule_matches:
                add_score = rule.score_item + (rule.score / len(rule_matches))
                for rule_match in rule_matches:
                    name = self._match_get_name(rule_match, rule.model)
                    if rule.model == 'account.invoice': so_ref = rule_match.origin or ''
                    elif rule.model == 'sale.order': so_ref = rule_match.name
                    else: so_ref = ''
                    description = self._match_description(rule_match, rule.model)
                    matches = self._update_match_list(
                        {'name': name,
                         'model': rule.model,
                         'description': description,
                         'so_ref': so_ref,},
                        add_score, matches)
        _logger.debug("1200wd - Search matches - match rules - %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        matches = [m for m in matches if m['score'] > 0]
        # Punish unknown references
        time_start = datetime.now()
        for match in [m for m in matches]:
            if not self._match_get_object(match['model'], match['name']):
                if match['score'] > 1:
                    match['score'] = 1

        # Calculate bonuses for already found matches
        for rule in self.env['account.bank.match.rule'].search(
                ['|', ('company_id', '=', False), ('company_id', '=', company_id),
                ('type', '=', 'bonus')]):
            rule_domain = self._parse_rule(rule)
            for match in [m for m in matches if m['model'] == rule.model]:
                if self._match_get_object(match['model'], match['name'], rule_domain):
                    match['score'] += rule.score_item
        _logger.debug("1200wd - Search matches - bonus rules - %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        # Sort and cleanup and return results
        time_start = datetime.now()
        matches = sorted(matches, key=lambda k: k['score'], reverse=True)
        matches = [m for m in matches if m['score'] > 0]
        _logger.debug("1200wd - Search matches - cleanup - %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))

        return matches


    # Check if there is a winning match. Assumes sorted list on descending score
    @api.model
    def _get_winning_match(self, matches):
        """
        @param matches: List of all matches found
        @return: Sale order reference and invoice reference of winning match
        """
        if matches and matches[0]['score'] >= MATCH_MIN_SUCCESS_SCORE and \
                (len(matches) == 1 or matches[1]['score'] <=MATCH_MIN_SUCCESS_SCORE or
                matches[1]['score'] < (matches[0]['score']-(MATCH_MIN_SUCCESS_SCORE / 2))):
            return (matches[0]['so_ref'], matches[0]['name'])
        else:
            return ('', '')


    @api.model
    def pay_invoice_and_reconcile(self, invoice, writeoff_acc_id, writeoff_difference=True, type=''):
        """
        Link this bank statement line to given invoice and write of differences if any to given writeoff account id
        @param invoice: invoice object
        @param writeoff_acc_id: account number where to write off
        @return: Move id of created move object
        """
        if len(invoice) != 1:
            self._handle_error("Can only pay one invoice at a time")
            return False
        if not invoice.residual:
            self._handle_error("Invoice %s has been payed already" % invoice.number or '')
            return False

        SIGN = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
        inv_direction = SIGN[invoice.type]
        date = self.date or self._context.get('date_p') or fields.Date.context_today(self)

        # Take the amount in currency and the currency of the payment
        if self._context.get('amount_currency') and self._context.get('currency_id'):
            amount_currency = self._context['amount_currency']
            currency_id = self._context['currency_id']
        else:
            amount_currency = False
            currency_id = False

        if invoice.type in ('in_invoice', 'in_refund'):
            ref = invoice.reference
        else:
            ref = invoice.number
        partner = invoice.partner_id

        if partner.parent_id:
            partner = partner.parent_id
        name = invoice.number or invoice.invoice_line[0].name
        pay_amount = self.amount
        period_id = self.statement_id.period_id.id
        invoice_total = inv_direction * invoice.residual
        pay_account_id = self.account_id.id or self.statement_id.account_id.id or 0
        pay_journal_id = self.journal_id.id or self.statement_id.journal_id.id or 0
        payment_difference = round(invoice_total + pay_amount, self.env['decimal.precision'].precision_get('Account'))

        # Skip reconciling if auto-matching and difference is too big
        configs = self.env['account.config.settings'].get_default_bank_match_configuration(self)
        writeoff_max_perc = configs.get('match_writeoff_max_perc')
        if writeoff_difference and type=='auto' and \
                        (abs(payment_difference / invoice_total) * 100) > writeoff_max_perc:
            msg = "Payment difference too big to automatically reconcile"
            self._handle_error(msg)
            return False

        move_lines = []
        move_lines.append((0, 0, {
            'name': name,
            'debit': pay_amount > 0 and pay_amount,
            'credit': pay_amount < 0 and -pay_amount,
            'account_id': pay_account_id,
            'partner_id': partner.id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': amount_currency or 0.0,
            'company_id': invoice.company_id.id,
        }))
        if payment_difference and writeoff_acc_id and writeoff_difference:
            move_lines.append((0, 0, {
                'name': name,
                'debit': payment_difference < 0 and -payment_difference,
                'credit': payment_difference > 0 and payment_difference,
                'account_id': writeoff_acc_id,
                'partner_id': partner.id,
                'ref': ref,
                'date': date,
                'currency_id': currency_id,
                'amount_currency': amount_currency or 0.0,
                'company_id': invoice.company_id.id,
            }))
            mv2_debit = invoice_total > 0 and invoice_total
            mv2_credit = invoice_total < 0 and -invoice_total
        else:
            mv2_debit = pay_amount < 0 and -pay_amount
            mv2_credit = pay_amount > 0 and pay_amount

        move_lines.append((0, 0, {
            'name': name,
            'debit': mv2_debit,
            'credit': mv2_credit,
            'account_id': invoice.account_id.id,
            'partner_id': partner.id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': inv_direction * (amount_currency or 0.0),
            'company_id': invoice.company_id.id,
        }))
        move = self.env['account.move'].create({
            'ref': ref,
            'line_id': move_lines,
            'journal_id': pay_journal_id,
            'period_id': period_id,
            'date': date,
        })

        move_ids = (move | invoice.move_id).ids
        self._cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s",
                         (tuple(move_ids),))
        lines = self.env['account.move.line'].browse([r[0] for r in self._cr.fetchall()])
        lines2rec = lines.browse()
        for line in itertools.chain(lines, invoice.payment_ids):
            if line.account_id == invoice.account_id:
                lines2rec += line

        if payment_difference and writeoff_difference and not writeoff_acc_id:
            msg = "Please select account to writeoff differences"
            self._handle_error(msg)
            return False
        elif not payment_difference or (payment_difference and writeoff_acc_id and writeoff_difference):
            # Pay and reconcile invoice, book payment differences
            r_id = self.env['account.move.reconcile'].create(
                {'type': 'auto',
                 'line_id': map(lambda x: (4, x, False), lines2rec.ids),
                 'line_partial_ids': map(lambda x: (3, x, False), lines2rec.ids)
                 }
            )
            for id in move_ids:
                workflow.trg_trigger(self._uid, 'account.move.line', id, self._cr)
        elif type == 'auto':
            msg = "Cannot partially pay invoices when auto-matching"
            self._handle_error(msg)
            return False
        else: # Payment difference, but do not writeoff_differences
            # Partially pay invoice, leave invoice open
            code = invoice.currency_id.symbol
            msg = _("Invoice partially paid: %s%s of %s%s (%s%s remaining).") % \
                    (pay_amount, code, invoice.amount_total, code, payment_difference, code)
            invoice.message_post(body=msg)
            lines2rec.reconcile_partial('manual')

        # Update the stored value (fields.function), so we write to trigger recompute
        invoice.write({})
        return move


    @api.one
    def create_account_move(self, account_id):
        """
        Create an account move from current bank statement line to specified account.
        Use date, amount, partner etc from this statement line.

        @param account_id: account_account id
        @return: newly created move object
        """
        account = self.env['account.account'].browse([account_id])
        date = self.date or self._context.get('date_p') or fields.Date.context_today(self)
        if self._context.get('amount_currency') and self._context.get('currency_id'):
            amount_currency = self._context['amount_currency']
            currency_id = self._context['currency_id']
        else:
            amount_currency = False
            currency_id = False
        ref = self.ref or self.name
        ref = ref[:30]
        partner_id = self.partner_id.id or 0
        name = account.code
        pay_amount = self.amount
        period_id = self.statement_id.period_id.id
        pay_account_id = self.account_id.id or self.statement_id.account_id.id or 0
        pay_journal_id = self.journal_id.id or self.statement_id.journal_id.id or 0
        move_lines = []
        move_lines.append((0, 0, {
            'name': name,
            'debit': pay_amount > 0 and pay_amount,
            'credit': pay_amount < 0 and -pay_amount,
            'account_id': pay_account_id,
            'partner_id': partner_id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': amount_currency or 0.0,
            'company_id': self.company_id.id,
        }))
        move_lines.append((0, 0, {
            'name': name,
            'debit': pay_amount < 0 and -pay_amount,
            'credit': pay_amount > 0 and pay_amount,
            'account_id': account_id,
            'partner_id': partner_id,
            'ref': ref,
            'date': date,
            'currency_id': currency_id,
            'amount_currency': -1 * (amount_currency or 0.0),
            'company_id': self.company_id.id,
        }))
        move = self.env['account.move'].create({
            'ref': ref,
            'line_id': move_lines,
            'journal_id': pay_journal_id,
            'period_id': period_id,
            'date': date,
        })
        _logger.info("1200wd - Created new account move with id %s, ref %s" % (move.id, ref))
        self.journal_entry_id = move.id
        return move.id


    @api.multi
    def account_bank_match(self, always_refresh=True):
        """
        === ACCOUNT BANK MATCH ===

        Calls match_search function if no recent matches are found in match table.
        Store match results in match table and return results.

        @param always_refresh: Always clear cache
        @return: number of matches found and winning match references
        """
        matches_found = 0
        so_ref = ''
        invoice_ref = ''
        for sl in self:
            # First check if any recent matches are still in cache ...
            configs = self.env['account.config.settings'].get_default_bank_match_configuration(self)
            match_cache_time = configs.get('match_cache_time')
            if match_cache_time != -1:
                to_old =  ((datetime.now() - timedelta(seconds=match_cache_time)).strftime('%Y-%m-%d %H:%M:%S'))
                matches_found = self.env['account.bank.match'].search_count([('statement_line_id', '=', sl.id), ('create_date', '>', to_old)])
            if matches_found and not always_refresh:
                matches = self.env['account.bank.match'].search_read([('statement_line_id', '=', sl.id)], order='score DESC', limit=2)

            # ... otherwise search for matches add them to database
            else:
                matches = sl.match_search()
                if matches:
                    matches_found = len(matches)
                    for match in matches:
                        data = {
                            'name': match['name'],
                            'model': match['model'],
                            'statement_line_id': sl.id,
                            'description': match.get('description', False),
                            'so_ref': match['so_ref'],
                            'score': match['score'] or 0,
                        }
                        self.env['account.bank.match'].create(data)

            so_ref, invoice_ref = sl._get_winning_match(matches)
        return {'matches_found': matches_found, 'so_ref': so_ref, 'name': invoice_ref}


    @api.multi
    def action_match_refresh(self):
        return self.action_statement_line_match(always_refresh=True)

    @api.multi
    def action_statement_line_match(self, always_refresh=False):
        """
        Action for web interface to trigger match update and open view with matches.

        @return: view with list of found matches
        """
        self.ensure_one()
        st_line = self[0]
        ctx = self._context.copy()
        ctx.update({
            'action_account_bank_match_view': True,
            'active_id': st_line.id,
            'active_ids': [st_line.id],
            'statement_line_id': st_line.id,
            })
        view = self.env.ref('account_bank_match.view_account_bank_statement_line_matches_form')
        match_result = self.account_bank_match(always_refresh=always_refresh)

        # if match_result['matches_found']:
        act_move = {
            'name': _('Match Bank Statement Line'),
            'res_id': st_line.id,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.statement.line',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'target': 'new',
            }
        act_move['context'] = dict(ctx, wizard_action=pickle.dumps(act_move))
        return act_move


    @api.one
    def match(self, vals):
        """
        If bank statement line is not matched yet call account_bank_match method.
        If a winning invoice match is found add invoice links to statement line.

        @param vals: Values of account.bank.statement.line to create or update
        @return: Updated list of values
        """
        if (not vals.get('name', False)) or vals.get('name', False) == '/':
            # Only search for matches if match_id not set
            if not ('match_selected' in vals and vals['match_selected']):
                match = self.account_bank_match(False)
                if match:
                    vals['so_ref'] = match['so_ref']
                    vals['name'] = match['name'] or '/'
                _logger.debug("1200wd - matching %s with vals %s" % (match, vals))
                vals = self.order_invoice_lookup(vals)
        return vals


    @api.one
    def auto_reconcile(self, type='auto'):
        """
        If there is an invoice linked to this bank statement line lookup writeoff difference account
        and call pay_invoice_and_reconcile method.

        When payment is processed and bank statement line reconciled update bank statement line with
        the id of new account move created.

        @return: Always True
        """
        time_start = datetime.now()
        configs = self.env['account.config.settings'].get_default_bank_match_configuration(self)
        if type == 'auto' and not configs.get('match_automatic_reconcile') or self.journal_entry_id:
            return True
        _logger.debug("1200wd - auto-reconcile journal %s" % self.name)
        if self.name and self.name != '/':
            invoice = self._match_get_object('account.invoice', self.name)
            if len(invoice) == 1:
                default_writeoff_journal_id = self.env['account.journal'].browse([configs.get('match_writeoff_journal_id')])
                if invoice.amount_total < 0:
                    writeoff_acc_id = self.match_selected.writeoff_difference and \
                                      (self.match_selected.writeoff_journal_id.default_debit_account_id.id or 0) or \
                                      (default_writeoff_journal_id.default_debit_account_id.id or 0)
                else:
                    writeoff_acc_id = self.match_selected.writeoff_difference and \
                                      (self.match_selected.writeoff_journal_id.default_credit_account_id.id or 0) or \
                                      (default_writeoff_journal_id.default_credit_account_id.id or 0)

                writeoff_difference = self.match_selected.writeoff_difference
                if type=='auto': writeoff_difference = True
                move_entry = self.pay_invoice_and_reconcile(invoice, writeoff_acc_id, writeoff_difference, type=type)
                if move_entry:
                    # Need to invalidate cache, otherwise changes in name are ignored
                    self.env.invalidate_all()
                    data = {
                        'journal_entry_id': move_entry.id,
                        'name': self.name or '/',
                        'so_ref': self.so_ref or '',
                        'partner_id': invoice.partner_id.id or '',
                    }
                    self.write(data)
                else:
                    return False
            else:
                msg = "Unique invoice with number %s not found, cannot reconcile" % self.name
                self._handle_error(msg)
                return False
        else:
            _logger.warning("1200wd - No reference name specified, cannot reconcile")
            return False
        _logger.debug("1200wd - Autoreconcile in %.0f milliseconds" %
                      ((datetime.now()-time_start).total_seconds() * 1000))
        return True


    @api.multi
    def action_match_reference_create(self):
        """
        Action for web interface to create new reference rule and open view.

        @return: view to create new reference extraction rule
        """
        st_line = self[0]
        ctx = self._context.copy()
        ref = re.sub(r"\s", "", st_line.ref).upper()
        remote_account = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id)]).sanitized_acc_number
        data = {
            'name': ref,
            'partner_bank_account': remote_account or '',
            'account_journal_id': st_line.journal_id.id,
            'company_id': st_line.company_id.id,
        }
        new_rm = self.env['account.bank.match.reference.create'].create(data)
        view = self.env.ref('account_bank_match.view_account_bank_match_reference_create_form')
        act_move = {
            'name': _('Match Reference Extraction Rule'),
            'res_id': new_rm.id,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.match.reference.create',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'target': 'new',
            }
        act_move['context'] = dict(ctx, wizard_action=pickle.dumps(act_move))
        return act_move


    @api.model
    def create(self, vals):
        statement_line = super(AccountBankStatementLine, self).create(vals)
        # TODO: Remove this method.
        return statement_line


    @api.multi
    def write(self, vals):
        # FIXME: Values are not saved anymore when removing this method
        return super(AccountBankStatementLine, self).write(vals)



class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.one
    def action_statement_match(self, show_errors=True):
        """
        Match all lines of this bank statement, if a winning match is found then process payment.
        If match_automatic_reconcile is set to true also reconcile.
        Automatically creates a invoice when payment received is matched to a sale order.

        This function can be very slow when running on large bank statement, or larger databases with invoices and
        orders. So it might be better in your situation to call this function with an external script instead of
        the Odoo web interface.

        @return: Always True, to avoid errors when calling to function with an RPC
        """
        _logger.info("1200wd - Match bank statement %d" % self.id)
        match_errors = []
        for line in [l for l in self.line_ids]:
            line.show_errors = False
            vals = line.read(['name', 'so_ref', 'match_selected', 'journal_entry_id'], False)[0]
            if not vals or vals['journal_entry_id']:
                continue
            try:
                vals_new = line.match(vals)
            except Exception, e:
                match_errors.append((line.id, line.ref, line.so_ref, e.message))
                continue
            if vals_new['name'] != '/':
                line.write(vals_new)
                line_match_ids = [l.id for l in line.match_ids]
                line_match = line_match_ids and self.env['account.bank.match'].search([('id', 'in', line_match_ids), ('name','=',vals_new['name'])])
                if line_match_ids and len(line_match) and line_match.model == 'account.account':
                    account_id = int(vals_new['name']) or 0
                    try:
                        line.create_account_move(account_id)
                    except Exception, e:
                        match_errors.append((line.id, line.ref, line.so_ref, e.message))
                        continue
                else:
                    try:
                        line.auto_reconcile()
                    except Exception, e:
                        match_errors.append((line.id, line.ref, line.so_ref, e.message))
                        continue

                _logger.info("1200wd - Matched bank statement line %s with %s" % (line.id, vals_new['name']))

        match_errors_str = ""
        for err in match_errors:
            match_errors_str += "Line ID: %d; Reference: %s, %s; Message: %s\n\n" % (err[0], err[1], err[2],err[3])
        if match_errors_str:
            if show_errors:
                raise Warning("Matching finished\nErrors matching the following statement lines:\n\n" + match_errors_str)
            else:
                return match_errors_str

        return True


    @api.model
    def create(self, vals):
        #FIXME: This is a quick fix to solve problems with a incorrect period in the bank statement. Find out why Odoo uses wrong period sometimes...
        try:
            period_id = self.onchange_date(vals['date'], self.env.user.company_id.id)['value']['period_id']
            vals['period_id'] = period_id
        except Exception, e:
            _logger.debug("1200wd - Could not fix period of statement %s. Error %s" % (vals['name'], e.args[0]))

        return super(AccountBankStatement, self).create(vals)