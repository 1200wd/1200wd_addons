# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Bank Match
#    Copyright (C) 2016 April
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

# TODO: Create function to write-off payment difference
# TODO: Filters on rule view
# TODO: Review and cleanup code
# TODO: Make installable: Create data files with rules
# TODO: Test on Noorderhaaks
# TODO: Test on Spieker

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
import re
import ast
import datetime
import pickle

_logger = logging.getLogger(__name__)

# Match module settings, normally there should be no need to change them...
MATCH_MIN_SUCCESS_SCORE = 100
MATCH_RULES_CACHE_MINUTES = 24*60
MATCH_AUTO_RECONCILE = True



class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def create_invoices(self, ids):
        """ Override to skip the wizard and invoice the whole sales order"""
        if not self._context.get('override', False):
            return super(SaleAdvancePaymentInv, self).create_invoices(ids)
        res = []
        sale_ids = self._context.get('order_ids', [])
        if sale_ids:
            res = self.env['sale.order'].manual_invoice(sale_ids)['res_id'] or []
        return res



class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    so_ref = fields.Char('Sale Order Reference')
    name = fields.Char('Communication', required=True, default='/')


    @api.one
    def _get_iban_country_code(self):
        if self.remote_account: self.remote_account_country_code = self.remote_account[:2]
        else: self.remote_account_country_code = ''

    remote_account_country_code = fields.Char(string="Remote IBAN country code", size=2, compute="_get_iban_country_code", readonly=True)


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
        _logger.debug("1200wd - account_bank_statement_line prepare_bs_line, invoice {}".format(invoice.number))
        if invoice.number:
            vals['name'] = invoice.number
        elif invoice.state == 'draft':
            invoice.signal_workflow('invoice_open')
            vals['name'] = invoice.number
        else:
            _logger.error("1200wd - account_bank_statement - Could not create or validate invoice for sale order {}!".format(vals['so_ref']))
        return vals


    @api.model
    def create_invoice(self):
        _logger.debug("1200wd - account_bank_statement_line create_invoice")
        adv_inv_obj = self.env['sale.advance.payment.inv']
        inv_obj = self.env['account.invoice']
        # Create invoice
        self._context['override'] = True
        invoice_id = adv_inv_obj.create_invoices()
        invoice = inv_obj.browse(invoice_id)
        # Validate invoice
        invoice.signal_workflow('invoice_open')
        return invoice


    @api.model
    def _prepare_create_invoice(self, order, vals):
        self._context.update({"order_ids": order.ids})
        invoice = self.create_invoice()
        # Add invoice reference to bank statement line
        return self.prepare_bs_line(invoice, vals)


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
                    _logger.error("1200wd - account_bank_statement - %s invoices found for orders: %s (ids)" % (len(invoices), so_ids))
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
                                    try:
                                        if vals['name'] == "/":
                                            vals['name'] = ''
                                            vals['name'] = invoice.number
                                        else:
                                            vals['name'] = ', '.join([vals['name'], invoice.number])
                                    except KeyError:
                                        vals['name'] = invoice.number
                    elif (order.order_policy == 'manual' and order.state == 'manual'):
                        vals = self._prepare_create_invoice(order, vals)
                    elif (order.order_policy == 'prepaid' and order.state != 'wait_payment'):
                        _logger.debug("1200wd - account_bank_statement - Trying to pay for Sale Order {} when its state is not 'Wait for Payment'.".format(vals['so_ref']))
                    else:
                        _logger.debug("1200wd - account_bank_statement - Create invoice skipped, order policy and state \
                         are {} and {} resp.".format(order.order_policy, order.state))
            else:
                _logger.error("%s sale orders found for reference: %s" % (len(order), vals['so_ref']))
                if len(order) > 1:
                    raise Warning(_("%s sale orders found for reference: %s" % (len(order), vals['so_ref'])))
        return vals


    @api.model
    def auto_reconcile(self):
        if not MATCH_AUTO_RECONCILE or self.journal_entry_id:
            return True
        _logger.debug("1200wd - auto-reconcile journal id %s, name %s" % (self.journal_entry_id.id, self.name))
        if self.name and self.name != "/":
            # import pdb; pdb.set_trace()
            ret = self.get_reconciliation_proposition(self)
            if ret:
                move_line = ret[0]
                payment_difference = (move_line['debit'] - move_line['credit']) - self.amount
                if payment_difference > 0.005:
                    _logger.warning(_("1200wd - Payment difference of %d for bank statement line %s. Cannot auto-reconcile" % (payment_difference, self.id)))
                    raise Warning("Payment difference of %.2f. Cannot reconcile" % payment_difference)
                    # ----- Create function to write-off payment difference. The process_reconciliation function does
                    #   not have any functionality to do this, so we need to create an own function to do this
                    #   see pay_and_reconcile method
                    # if payment_difference < 0: debit = 0; credit = payment_difference
                    # else: debit = payment_difference; credit = 0
                    # move_writeoff = {
                    #     'debit': debit,
                    #     'credit': credit,
                    # }
                move_dicts = [{
                    'counterpart_move_line_id': move_line['id'],
                    'debit': move_line['credit'],
                    'credit': move_line['debit'],
                }]
                self.process_reconciliation(move_dicts)
            else:
                raise Warning(_("Unknown reference %s, no reconciliation proposition found" % self.name))
        else:
            raise Warning(_("No reference name specified, cannot reconcile" % self.name))
        return True


    @api.model
    def _make_transfer(self, vals, account_name):
        journal_id = account_name
        move_vals = {
            'journal_id': journal_id,
            'name': vals['name'],
            'amount': vals['amount'],
            # 'amount_currency': vals['amount_currency'],
            'partner_id': vals['partner_id'],
            'date': vals['date'],
            # 'period_id': 1,
            # 'company_id': 1,
        }
        # import pdb; pdb.set_trace()
        # move_line_pool = self.pool.get('account.move.line')
        # move_pool = self.pool.get('account.move')
        # return move_pool.account_move_prepare(cr, uid, journal_id, context=context)


    @api.model
    def _extract_references(self):
        try:
            statement_text = (self.name or '') + '_' + (self.partner_id.name or '') + '_' + (self.ref or '') + '_' + (self.so_ref or '')
        except Exception, e:
            import pdb; pdb.set_trace()
        statement_text = re.sub(r"\W", "", statement_text).upper()
        company_id = self.env.user.company_id.id
        matches = []
        count = 0
        match_refs = self.env['account.bank.statement.match.reference'].search(['|', ('company_id', '=', False), ('company_id', '=', company_id)])
        for match_ref in match_refs:
            try:
                for m in re.finditer(match_ref.name, statement_text):
                    obj = self.env[match_ref.model].search([(self._match_get_field_name(match_ref.model), '=', m.group(0))])
                    description = self._match_description(obj, match_ref.model)
                    if match_ref.model == 'account.invoice': so_ref = obj.origin or ''
                    elif match_ref.model == 'sale.order': so_ref = m.group(0)
                    else: so_ref = ''
                    matches.append(
                        {'name': m.group(0),
                         'so_ref': so_ref,
                         'model': match_ref.model,
                         'description': description,
                         'score': match_ref.score,
                         'score_item': match_ref.score_item,
                         })
                    _logger.debug("1200wd - Match %s found" % m.group(0))
                    count += 1
                    if count > 100: break
            # except TypeError, e:
            except Exception, e:
                import pdb; pdb.set_trace()
                raise Warning(_("TypeError: Please check Bank Match Reference patterns an error occured while parsing '%s'. Error: %s" % (match_ref.name, e.args[0])))
        return matches


    @api.model
    def _parse_rule(self, rule):
        _logger.debug("1200wd - Running match rule %s" % rule.name)

        rule_list = []
        try:
            rule_list = ast.literal_eval(rule.rule)
        except Exception, e:
            _logger.error("1200wd - Could not parse rule '{}'. Error Message: {}".format(rule.rule, e.message))

        rule_list_new = []
        for field_name, operator, value in rule_list:
            # _logger.debug("1200wd - process {} {} {}".format(field_name, operator, value))
            new_value = None
            if isinstance(value, str):
                matches = re.search("@(.+?)@", value)
                if matches:
                    found_odoo_expression = matches.group(1)
                    if found_odoo_expression == 'None':
                        new_value = None
                    elif 'today' in found_odoo_expression:
                        numofdays = int(re.search("today-(\d+)", found_odoo_expression).group(1))
                        new_value = ((datetime.datetime.now() - datetime.timedelta(days=numofdays)).strftime('%Y-%m-%d'))
                    else:
                        odoo_expression = re.sub("@(.+?)@", "self." + found_odoo_expression, value)
                        try:
                            # !!!Please note!!!: This executes the string as python code, set security rules wisely!
                            new_value = eval(odoo_expression)
                            if not new_value:
                                continue
                        except Exception, e:
                            # import pdb; pdb.set_trace()
                            _logger.warning("1200wd - Rule '{}'. Error matching odoo expression '{}' {}".
                                            format(rule.rule, odoo_expression, e.message))
            if new_value:
                rule_list_new.append((field_name, operator, new_value))
            else:
                rule_list_new.append((field_name, operator, value))

        _logger.debug("1200wd - Parsing rule result %s" % rule_list_new)
        return rule_list_new


    @api.model
    def _update_match_list(self, match, add_score, matches=[]):
        if not 'so_ref' in match:
            import pdb; pdb.set_trace()

        # If match is an account move line ...
        if match['model'] == 'account.move.line':
            # aml = self._match_get_object('account.move.line', match['name'])
            # Add extra code for matching with move lines here, for now thou shall
            pass

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
                 'so_ref': match.get('so_ref', '')})
        else:
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
        description = ''
        try:
            currency_symbol = ''
            if 'currency_id' in object:
                currency_symbol = object.currency_id.name or ''
            if model == 'account.invoice':
                description = (object.number or 'Not found') + "; " + (object.origin or '') + "; " + (object.date_invoice or '') + "; " + (object.partner_id.name or '') + "; " + \
                              (object.state or '') + "; " + currency_symbol + " " + str(object.amount_total or '')
            elif model == 'account.move.line':
                description = (object.ref or 'Not found') + "; " + (object.date or '') + "; " + (object.partner_id.name or '') + "; " + \
                              (object.state or '') + "; " + currency_symbol + " " + str(object.debit or '')
            elif model == 'sale.order':
                description = (object.date_order or 'Not found') + "; " + (object.partner_id.name or '') + "; " + \
                              (object.state or '') + "; " + currency_symbol + " " + str(object.amount_total)
        except Exception, e:
            _logger.warning("1200wd - Could not construct match description. Error %s" % e.args[0])
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
        elif model == 'account.move.line':
            return 'date'
        elif model == 'sale.order':
            return 'date_order'
        else: return ''


    @api.model
    def _match_get_base_domain(self, model):
        daysback = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        company_id = self.env.user.company_id.id
        domain = ['|', ('company_id', '=', False), ('company_id', '=', company_id)]
        if model == 'sale.order':
            domain.extend([('date_order', '>', daysback),
                           ('state', 'in', ['draft', 'wait_payment', 'sent', 'done'])])
        elif model == 'account.invoice':
            domain.extend([('date_invoice', '>', daysback),
                           ('state', 'in', ['open'])])
        elif model == 'account.move.line':
            domain.extend([('date', '>', daysback), ('reconcile_ref', '=', False)])

        return domain


    @api.model
    def _match_get_object(self, model, ref, domain = None):
        if domain is None:
            domain = []
        try:
            m = self.env[model]
            if model == 'account.invoice':
                return m.search([('number', '=', ref)] + domain)
            elif model == 'sale.order':
                return m.search([('name', '=', ref)] + domain)
            else:
                return m.search([('id', '=', ref)] + domain)

        except Exception, e:
            _logger.error("1200wd - Could not open model %s with reference %s. Error %s" % (model, ref, e.args[0]))
        return False


    @api.model
    def match_search(self):
        # Delete old match records
        try:
            self._cr.execute("DELETE FROM account_bank_statement_match WHERE statement_line_id=%d" % self.id)
            self.invalidate_cache()
        except AttributeError:
            return False

        company_id = self.env.user.company_id.id

        # Try to find partner through bank account number
        if not self.partner_id and self.remote_account:
            bank = self.env['res.partner.bank'].search([('search_account_number', '=', self.remote_account)])
            if bank.partner_id:
                self.partner_id = bank.partner_id
            else:
                # Look for other statement lines from the same remote bank account and see if any of those have partners and invoices linked
                other_lines = self.env['account.bank.statement.line'].search(['|', ('company_id', '=', False), ('company_id', '=', company_id),
                    ('remote_account','=',bank.search_account_number), ('id', '!=', self.id)], limit=1)
                if 'partner_id' in other_lines and other_lines.partner_id:
                    self.partner_id = other_lines.partner_id

        # Search matches with reference pattern
        company_id = self.env.user.company_id.id
        matches = []
        ref_matches = self._extract_references()
        if ref_matches:
            base_score = sum([d['score'] for d in ref_matches]) / len(ref_matches)
            for ref_match in ref_matches:
                matches = self._update_match_list(ref_match, base_score + ref_match['score_item'], matches)

        # Run match rules on invoices, sale orders and account.moves
        for rule in self.env['account.bank.statement.match.rule'].search(
                ['|', ('company_id', '=', False), ('company_id', '=', company_id),
                ('type', '=', 'extraction')]):
            rule_domain = self._parse_rule(rule)
            if not rule_domain: # stop running rule if empty domain is returned to avoid useless matches on rule parsing errors
                continue
            base_domain = self._match_get_base_domain(rule['model'])
            orderby_field = self._match_get_datefield_name(rule['model'])
            if orderby_field: orderby_field += ' DESC'
            rule_matches = self.env[rule['model']].search(base_domain + rule_domain, limit=25, order=orderby_field)
            _logger.debug("1200wd - %d matches found" % len(rule_matches))
            if rule_matches:
                add_score = rule['score_item'] + (rule['score'] / len(rule_matches))
                for rule_match in rule_matches:
                    name = self._match_get_name(rule_match, rule['model'])
                    if rule['model'] == 'account.invoice': so_ref = rule_match.origin or ''
                    elif rule['model'] == 'sale.order': so_ref = rule_match.name
                    else: so_ref = ''
                    description = self._match_description(rule_match, rule['model'])
                    matches = self._update_match_list(
                        {'name': name,
                         'model': rule['model'],
                         'description': description,
                         'so_ref': so_ref},
                        add_score, matches)

        # Calculate bonuses for already found matches
        for rule in self.env['account.bank.statement.match.rule'].search(
                ['|', ('company_id', '=', False), ('company_id', '=', company_id),
                ('type', '=', 'bonus')]):
            rule_domain = self._parse_rule(rule)
            for match in [m for m in matches if m['model'] == rule['model']]:
                if self._match_get_object(match['model'], match['name'], rule_domain):
                    match['score'] += rule['score_item']
                    _logger.debug("1200wd - Bonus found %s %s" % (rule.name, match))

        # Sort and cleanup and return results
        matches = sorted(matches, key=lambda k: k['score'], reverse=True)
        matches = [m for m in matches if m['score'] > 0]

        return matches


    # Check if there is a winning match. Assumes sorted list on descending score
    @api.model
    def _get_winning_match(self, matches):
        if matches and matches[0]['score'] > MATCH_MIN_SUCCESS_SCORE and \
                (len(matches) == 1 or matches[1]['score'] <=MATCH_MIN_SUCCESS_SCORE or
                matches[1]['score'] < (matches[0]['score']-(MATCH_MIN_SUCCESS_SCORE / 2))):
            return (matches[0]['so_ref'], matches[0]['name'])
        else:
            return ('', '')


    @api.multi
    def account_bank_match(self, always_refresh=True):
        matches_found = 0
        so_ref = ''
        invoice_ref = ''
        for sl in self:
            # First check if any recent matches are still in cache ...
            to_old =  ((datetime.datetime.now() - datetime.timedelta(minutes=MATCH_RULES_CACHE_MINUTES)).strftime('%Y-%m-%d %H:%M'))
            matches_found = self.env['account.bank.statement.match'].search_count([('statement_line_id', '=', sl.id), ('create_date', '>', to_old)])
            if matches_found and not always_refresh:
                matches = self.env['account.bank.statement.match'].search_read([('statement_line_id', '=', sl.id)], order='score DESC', limit=2)

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
                        _logger.debug("1200wd - Match found %s: %s, score %d" % (match['name'], match.get('description', False), match['score'] or 0))
                        self.env['account.bank.statement.match'].create(data)

            so_ref, invoice_ref = sl._get_winning_match(matches)
        return {'matches_found': matches_found, 'so_ref': so_ref, 'name': invoice_ref}


    @api.multi
    def action_statement_line_match(self):
        st_line = self[0]
        ctx = self._context.copy()
        ctx.update({
            'action_account_bank_statement_match_view': True,
            'active_id': st_line.id,
            'active_ids': [st_line.id],
            'statement_line_id': st_line.id,
            })
        view = self.env.ref('account_bank_match.view_account_bank_statement_line_matches_form')
        match_result = self.account_bank_match(False)

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


    @api.model
    def _statement_line_match(self, vals):
        if (not vals.get('name', False)) or vals.get('name', False) == '/':
            # Only search for matches if match_id not set and if no sales order reference is known
            if not ('match_id' in vals and vals['match_id']) and not vals.get('so_ref', False):
                match = self.account_bank_match(False)
                if match:
                    vals['so_ref'] = match['so_ref']
                    vals['name'] = match['name'] or '/'
                _logger.debug("1200wd - matching %s with vals %s" % (match, vals))
                vals = self.order_invoice_lookup(vals)
        return vals


    @api.model
    def create(self, vals):
        """Override to look up Invoice Reference based on given Sale Order Reference."""
        statement_line = super(AccountBankStatementLine, self).create(vals)
        vals_new = statement_line._statement_line_match(vals)
        if vals != vals_new:
            super(AccountBankStatementLine, self).write(vals_new)
        return statement_line


    @api.multi
    def write(self, vals):
        """Override to look up Invoice Reference based on given Sale Order Reference."""
        vals = self._statement_line_match(vals)
        return super(AccountBankStatementLine, self).write(vals)



class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.one
    def action_statement_match(self):
        _logger.debug("1200wd - Match bank statement %d" % self.id)
        for line in [l for l in self.line_ids]:
            vals = line.read([], False)
            # Match statement line with invoice or created invoice from sale order.
            vals_new = line._statement_line_match(vals[0])
            if vals[0] != vals_new:
                _logger.debug("1200wd - Match bank statement line with values %s" % vals_new)
                line.write(vals_new)
            line.auto_reconcile()
