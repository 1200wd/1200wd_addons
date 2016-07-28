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

import logging
from openerp import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        # Call super function and change tax depending on Sales Channel
        result = super(SaleOrderLine, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos,
                                                                uos, name, partner_id, lang, update_tax, date_order,
                                                                packaging, fiscal_position, flag, context)
        if product:
            context_partner = {'lang': lang, 'partner_id': partner_id}
            product_obj = self.pool.get('product.product').browse(cr, uid, product, context=context_partner)

            # Use Partner to get Sales Channel and Company ID because Sale Order ID is unknown
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner.sales_channel_id.id:
                tids = self.pool['account.tax'].search(cr, uid, [
                    ('amount', '=', product_obj.taxes_id.amount),
                    ('company_id', '=', partner.company_id.id),
                    ('type_tax_use', '=', 'sale'),
                    ('sales_channel_id', '=', partner.sales_channel_id.id)], context=context)

                fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)
                found = False
                t = False
                for tid in tids:
                    t = self.pool['account.tax'].browse(cr, uid, tid)
                    for ftid in fpos.tax_ids:
                        if ftid.tax_src_id.id == t.id:
                            _logger.debug("1200wd - Tax found {}, fiscal position {}".format(t.id, fiscal_position))
                            found = True
                if not found:
                    try:
                        # import pdb; pdb.set_trace()
                        if t and result['value']['tax_id'][0] != t.id:
                            _logger.debug("1200wd - Changed to Sales Channel {} specific tax {}".
                                          format(partner.sales_channel_id.id, t.id))
                            result['value']['tax_id'][0] = t.id
                    except Exception, e:
                        _logger.warning("1200wd - Could not update tax. Error: {}".format(e.message))

        return result


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_sales_channel_domain(self):
        ids = []
        try:
            ids = self.env.ref('ari_sale.category_sales_channel').ids
        except ValueError:
            pass
        return [('category_id', 'in', ids)]

    sales_channel_id = fields.Many2one('res.partner', string="Sales channel", ondelete='set null',
                                       domain=_get_sales_channel_domain, required=True, index=True)

    @api.onchange('sales_channel_id')
    def sales_channel_change(self):
        if self.sales_channel_id.property_product_pricelist:
            self.pricelist_id = self.sales_channel_id.property_product_pricelist

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)

        if partner_id:
            res['value'].update({
                'sales_channel_id': partner.sales_channel_id,
                'pricelist_id': partner.sales_channel_id.property_product_pricelist,
            })
        return res

    @api.model
    def _prepare_invoice(self, order, lines, context=None):
        _logger.debug('1200wd sale_channel prepare_invoice')
        val = super(SaleOrder, self)._prepare_invoice(order, lines, context=context)

        if order.sales_channel_id:
            val.update({
                'sales_channel_id': order.sales_channel_id.id,
            })

        return val
