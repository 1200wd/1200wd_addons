# -*- coding: utf-8 -*-
#
#    Account Bank Match - Init Hooks
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

import logging
from openerp import SUPERUSER_ID
from openerp.api import Environment

_logger = logging.getLogger(__name__)


def post_init_hook(cr, pool):
    env = Environment(cr, SUPERUSER_ID, {})
    action_generate_references(env)


def action_generate_references(env):
    aj = env['account.journal'].search(
        [('type', 'in', ['sale', 'sale_refund', 'purchase', 'purchase_refund'])])
    for journal in aj:
        seq = journal.sequence_id
        if not seq.prefix and not seq.suffix:
            continue
        ref_pat = (seq.prefix or '') + '[0-9]{' + str(seq.padding) + '}' + (seq.suffix or '')

        ref_obj = env['account.bank.match.reference'].search(
            [('name', '=', ref_pat), ('company_id', '=', journal.company_id.id)])
        ref_seq = 10
        if 'refund' in journal.type:
            ref_seq += 5
        data = {
            'name': ref_pat,
            'model': 'account.invoice',
            'sequence': ref_seq,
            'score': 75,
            'score_item': 20,
            'company_id': journal.company_id.id,
        }
        if not len(ref_obj):
            _logger.debug("1200wd - Create match reference %s" % data)
            env['account.bank.match.reference'].create(data)
        elif len(ref_obj) == 1:
            _logger.debug("1200wd - Update match reference %s" % data)
            ref_obj.write(data)
        else:
            _logger.warning("1200wd - More then 1 match reference already exist: %s" % data)
