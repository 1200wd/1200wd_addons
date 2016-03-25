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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
import re
import ast
import datetime
import pickle

_logger = logging.getLogger(__name__)


class sale_advance_payment_inv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self, cr, uid, ids=[], context=None):
        """ Override to skip the wizard and invoice the whole sales order"""
        if not context.get('override', False):
            return super(sale_advance_payment_inv, self).create_invoices(cr, uid, ids, context=context)
        res = []
        sale_obj = self.pool.get('sale.order')
        sale_ids = context.get('order_ids', [])
        if sale_ids:
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)['res_id'] or []
        return res


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    so_ref = fields.Char('Sale Order Reference')
    name = fields.Char('Communication', required=True, default='/')

    def _domain_reconciliation_proposition(self, cr, uid, st_line, excluded_ids=None, context=None):
        if excluded_ids is None:
            excluded_ids = []
        domain = ['|', ('ref', '=', st_line.name),
                       ('move_id.name', '=', st_line.name),
                  ('reconcile_id', '=', False),
                  ('state', '=', 'valid'),
                  ('account_id.reconcile', '=', True),
                  ('id', 'not in', excluded_ids)]
        return domain

    def lookup_invoice(self, cr, uid, so_id, context):
        so_obj = self.pool.get('sale.order')
        so = so_obj.browse(cr, uid, so_id, context=context)
        return so.invoice_ids

    def prepare_bs_line(self, cr, uid, invoice, vals, context=None):
        _logger.debug("1200wd - account_bank_statement_line prepare_bs_line, invoice {}".format(invoice.number))
        if invoice.number:
            vals['name'] = invoice.number
        elif invoice.state == 'draft':
            invoice.signal_workflow('invoice_open')
            vals['name'] = invoice.number
        else:
            _logger.error("1200wd - account_bank_statement - Could not create or validate invoice for sale order {}!".format(vals['so_ref']))
        return vals

    def create_invoice(self, cr, uid, context=None):
        _logger.debug("1200wd - account_bank_statement_line create_invoice")
        adv_inv_obj = self.pool.get('sale.advance.payment.inv')
        inv_obj = self.pool.get('account.invoice')
        # Create invoice
        context['override'] = True
        invoice_id = adv_inv_obj.create_invoices(cr, uid, context=context)
        invoice = inv_obj.browse(cr, uid, invoice_id, context=context)
        # Validate invoice
        invoice.signal_workflow('invoice_open')
        return invoice

    def _prepare_create_invoice(self, cr, uid, order, vals, context=None):
        context.update({"order_ids": order.ids})
        invoice = self.create_invoice(cr, uid, context=context)
        # Add invoice reference to bank statement line
        return self.prepare_bs_line(cr, uid, invoice, vals, context=context)

    def order_invoice_lookup(self, cr, uid, vals, context=None):
        """Find the invoice reference for the given order reference. Create an invoice if applicable."""
        if vals.get('so_ref', None):
            so_obj = self.pool.get('sale.order')
            so_ids = so_obj.search(cr, uid, [('name', '=', vals['so_ref'])], context=context)
            if len(so_ids) == 1:
                order = so_obj.browse(cr, uid, so_ids[0], context=context)
                invoices = self.lookup_invoice(cr, uid, so_ids[0], context=context)

                if len(invoices) == 1:
                    vals = self.prepare_bs_line(cr, uid, invoices[0], vals, context=context)
                elif len(invoices) > 1:
                    _logger.error("1200wd - account_bank_statement - %s invoices found for orders: %s (ids)" % (len(invoices), so_ids))
                else:
                    # Create invoice
                    if (order.order_policy == 'prepaid' or order.order_policy == 'manual') \
                            and order.state == 'wait_payment':
                        if order.signal_workflow('order_confirm'):
                            if order.order_policy == 'manual':
                                vals = self._prepare_create_invoice(cr, uid, order, vals, context=context)
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
                        vals = self._prepare_create_invoice(cr, uid, order, vals, context=context)
                    elif (order.order_policy == 'prepaid' and order.state != 'wait_payment'):
                        _logger.debug("1200wd - account_bank_statement - Trying to pay for Sale Order {} when its state is not 'Wait for Payment'.".format(vals['so_ref']))
                    else:
                        _logger.debug("1200wd - account_bank_statement - Create invoice skipped, order policy and state \
                         are {} and {} resp.".format(order.order_policy, order.state))
            else:
                _logger.error("%s sale orders found for reference: %s" % (len(so_ids), vals['so_ref']))
                if len(so_ids) > 1:
                    raise Warning(_("%s sale orders found for reference: %s" % (len(so_ids), vals['so_ref'])))
        return vals

    @api.one
    def auto_reconcile(self):
        _logger.debug("1200wd - auto-reconcile journal id %s, name %s" % (self.journal_entry_id.id, self.name))
        if not self.journal_entry_id and self.name and self.name != "/":
            ret = self.get_reconciliation_proposition(self)
            if ret:
                move_line = ret[0]
                if move_line['debit'] == self.amount or move_line['credit'] == -self.amount:
                    move_dicts = [{
                        'counterpart_move_line_id': move_line['id'],
                        'debit': move_line['credit'],
                        'credit': move_line['debit'],
                    }]
                    self.process_reconciliation(move_dicts)
        return True

    def _make_transfer(self, cr, uid, vals, account_name, context=None):
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

    def _extract_references(self):
        statement_text = self.name or '' + self.partner_id.name or ''  + self.ref or '' + self.so_ref or ''
        statement_text = re.sub(r"\W", "", statement_text).upper()
        company_id = self.env.user.company_id.id
        matches = []
        count = 0
        match_refs = self.env['account.bank.statement.match.reference'].search(['|', ('company_id', '=', False), ('company_id', '=', company_id)])
        for match_ref in match_refs:
            for m in re.finditer(match_ref.reference_pattern, statement_text):
                matches.append({'name': m.group(0), 'type': match_ref.type, 'description': ''})
                count += 1
                if count > 100: break
        return matches

    def _statement_line_match(self, cr, uid, vals, context=None):
        if 'name' not in vals:
            return vals
        if (not vals.get('name', False)) or vals.get('name', False) == '/':
            if not vals.get('so_ref', False):
                vals = self._extract_references(cr, uid, vals, context=context)
            vals = self.order_invoice_lookup(cr, uid, vals, context)
        return vals

    def _parse_rule(self, rule):
        _logger.debug("1200wd - Running match rule %s" % rule)

        try:
            rule_list = ast.literal_eval(rule.rule)
        except Exception, e:
            _logger.error("1200wd - Could not parse rule '{}'. Error Message: {}".format(rule.rule, e.message))

        rule_list_new = []
        for field_name, operator, value in rule_list:
            _logger.debug("1200wd - process {} {} {}".format(field_name, operator, value))
            new_value = None
            if isinstance(value, str):
                matches = re.search("@(.+?)@", value)
                if matches:
                    found_odoo_expression = matches.group(1)
                    _logger.debug("1200wd - found_odoo_expression {}".format(found_odoo_expression))
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
                        except Exception, e:
                            _logger.warning("1200wd - Rule '{}'. Error matching odoo expression '{}' {}".
                                            format(rule.rule, odoo_expression, e.message))
            if new_value:
                rule_list_new.append((field_name, operator, new_value))
            else:
                rule_list_new.append((field_name, operator, value))

        _logger.debug("1200wd - rule_list_new %s" % rule_list_new)
        return rule_list_new
        #Bedrag (incl datum, status(open))
        # -zoek account.move op bedrag: precies, afrondings verschillen en +/- x%
        # -zoek sale.order op bedrag: precies, afrondings verschillen en +/- x%
        # -zoek invoice op bedrag: precies, afrondings verschillen en +/- x%
        #PARTNER
        # zoek partner op iban
        # zoek partner op naam
    #(2) Geef score en voeg samen in match tabel:
        #  - type (sale.order, account.invoice, account.account
        #  - referentie
        #  - statement-line-id
        #  - score
        #  - gematchte regel

    def _update_match_list(self, match, add_score, matches=[]):
        # If match to a sale order and sale order has an invoice then replace match with invoice number
        if match['type'] == 'sale.order':
            invoice = self.env['sale.order'].search([('name', '=', match['name'])]).invoice_ids
            # TODO: Handle situation where 1 sale orders has multiple invoices or other n-m relations
            if len(invoice) == 1:
                match['description'] += ";" + match['name']
                match['type'] = 'account.invoice'
                match['name'] = invoice.number or ''

        # Remove duplicates and sum up scores
        if match['name'] not in [d['name'] for d in matches]:
            matches.append({'name': match['name'], 'type': match['type'], 'score': add_score, 'description': match.get('description', '')})
        else:
            [d.update({'score': d['score'] + add_score}) for d in matches if d['name'] == match['name']]

        return matches

    def account_bank_match(self):
        # Delete old match records
        self._cr.execute("DELETE FROM account_bank_statement_match WHERE statement_line_id=%d" % self.id)
        self.invalidate_cache()

        # Search matches with reference pattern
        matches = []
        ref_matches = self._extract_references()
        if ref_matches:
            add_score = (75 / len(ref_matches)) + 25
            for ref_match in ref_matches:
                matches = self._update_match_list(ref_match, add_score, matches)

        # Search for amount in invoices, sale orders and account.moves
        for rule in self.env['account.bank.statement.match.rule'].search([]):
            rule_list = self._parse_rule(rule)
            daysback = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
            if rule['type'] == 'sale.order': datefield = 'date_order'
            elif rule['type'] == 'account.invoice': datefield = 'date_invoice'
            else: datefield = 'date'
            rule_matches = self.env[rule['type']].search([(datefield, '>', daysback)] + rule_list, order=datefield+' DESC', limit=25)
            if rule_matches:
                add_score = rule['score'] / len(rule_matches)
                for rule_match in rule_matches:
                    if rule['type'] == 'account.invoice':
                        name = rule_match.number
                        description = rule_match.origin + "; " + rule_match.date_invoice + "; " + rule_match.partner_id.name + "; " + str(rule_match.amount_total)
                    elif rule['type'] == 'account.move.line':
                        name = rule_match.id
                        description = rule_match.ref + "; " + rule_match.date + "; " + rule_match.partner_id.name + "; " + str(rule_match.debit)
                    elif rule['type'] == 'sale.order':
                        name = rule_match.name
                        description = rule_match.date_order + "; " + rule_match.partner_id.name + "; " + str(rule_match.amount_total)
                    matches = self._update_match_list({'name': name, 'type': rule['type'], 'description': description}, add_score, matches)


        for match in matches:
            data = {
                'name': match['name'],
                'type': match['type'],
                'statement_line_id': self.id,
                'description': match.get('description', False),
                'score': match['score'] or 0,
            }
            self.env['account.bank.statement.match'].create(data)
        # _logger.debug("1200wd - Normalized and Weight Matches %s" % matches)

        #(3) 1 gevonden met score >100 match automatisch
            # invoice gaat voor sale.order
        return True




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
        viewt = self.env.ref('account_bank_match.view_account_bank_statement_match_tree')
        viewf = self.env.ref('account_bank_match.view_account_bank_statement_match_form')
        act_move = True
        if self.account_bank_match():
            act_move = {
                'name': _('Match Bank Statement Line'),
                'res_id': st_line.id,
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.bank.statement.match',
                'type': 'ir.actions.act_window',
                'views': [(viewt.id, 'tree'), (viewf.id, 'form')],
                'target': 'new',
                }
            act_move['context'] = dict(ctx, wizard_action=pickle.dumps(act_move))
        return act_move


    def create(self, cr, uid, vals, context=None):
        """Override to look up Invoice Reference based on given Sale Order Reference."""
        vals = self._statement_line_match(cr, uid, vals, context)
        return super(account_bank_statement_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """Override to look up Invoice Reference based on given Sale Order Reference."""
        vals = self._statement_line_match(cr, uid, vals, context)
        return super(account_bank_statement_line, self).write(cr, uid, ids, vals, context=context)




class account_bank_statement(models.Model):
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

